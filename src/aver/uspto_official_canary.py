#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

URL="https://tmsearch.uspto.gov/"
CASES=[
    {"name":"KNOWN_POSITIVE_SINGLE_TERM","query":"NIKE","expected":"POSITIVE"},
    {"name":"OPAQUE_ZERO_SINGLE_TERM","query":"QZXJVMRKPLN91372","expected":"ZERO"},
]


def text(page):
    try:
        return re.sub(r"\s+"," ",page.locator("body").inner_text(timeout=5000)).strip()
    except Exception:
        return ""


def select_wordmark(page):
    evidence=[]
    # Native select, if the current UI exposes one.
    for sel in ["select"]:
        try:
            loc=page.locator(sel)
            for i in range(min(loc.count(),10)):
                el=loc.nth(i)
                if not el.is_visible():
                    continue
                opts=[]
                try: opts=el.locator("option").all_text_contents()
                except Exception: pass
                if any("wordmark" in (x or "").lower() for x in opts):
                    for opt in opts:
                        if "wordmark" in (opt or "").lower():
                            el.select_option(label=opt)
                            page.wait_for_timeout(300)
                            return {"selected":True,"method":"select_option","label":opt,"options":opts[:20]}
        except Exception as exc:
            evidence.append(f"select:{type(exc).__name__}")
    # Button/dropdown UI.
    for opener in ["button:has-text('General search')","button:has-text('Wordmark')","text='General search'"]:
        try:
            loc=page.locator(opener)
            if loc.count() and loc.first.is_visible():
                loc.first.click(); page.wait_for_timeout(250)
                for option in ["text='Wordmark'","[role='option']:has-text('Wordmark')","button:has-text('Wordmark')"]:
                    op=page.locator(option)
                    for j in range(min(op.count(),10)):
                        if op.nth(j).is_visible():
                            op.nth(j).click(); page.wait_for_timeout(300)
                            return {"selected":True,"method":f"{opener}->{option}"}
        except Exception as exc:
            evidence.append(f"{opener}:{type(exc).__name__}")
    return {"selected":False,"attempts":evidence}


def choose_input(page):
    candidates=[]
    for selector in ["input","textarea"]:
        try:
            loc=page.locator(selector)
            for i in range(min(loc.count(),30)):
                el=loc.nth(i)
                if not el.is_visible(): continue
                try:
                    ph=el.get_attribute("placeholder") or ""
                    typ=el.get_attribute("type") or ""
                    candidates.append({"selector":selector,"index":i,"placeholder":ph,"type":typ})
                    blob=(ph+" "+typ).lower()
                    if "search" in blob or "wordmark" in blob:
                        return el,candidates
                except Exception: pass
        except Exception: pass
    return None,candidates


def probe(page,query):
    body=text(page)
    lower=body.lower()
    count=None
    m=re.search(r"([\d,]+)\s+results?\s+for",body,re.I)
    if m: count=int(m.group(1).replace(",",""))
    control=any(x in lower for x in ("captcha","verify you are human","are you a robot","access denied"))
    zero=(count==0) or "no results found" in lower or "no results" in lower
    positive=(count is not None and count>0)
    return {"count":count,"positive":positive,"zero":zero,"control":control,"query_visible":query.lower() in lower,"body_excerpt":body[:3500],"final_url":page.url}


def run_case(browser,case):
    page=browser.new_page(viewport={"width":1440,"height":1000})
    rec={**case,"state":"UNPROVEN","failure_signature":None}
    try:
        page.goto(URL,wait_until="domcontentloaded",timeout=30000); page.wait_for_timeout(1000)
        rec["wordmark_mode"]=select_wordmark(page)
        if not rec["wordmark_mode"].get("selected"):
            rec["failure_signature"]="USPTO_WORDMARK_MODE_NOT_BOUND"; return rec
        inp,candidates=choose_input(page); rec["input_candidates"]=candidates
        if inp is None:
            rec["failure_signature"]="USPTO_VISIBLE_SEARCH_INPUT_NOT_FOUND"; return rec
        inp.fill(case["query"]); page.wait_for_timeout(250)
        rec["pre_submit_value"]=inp.input_value(timeout=1500)
        if rec["pre_submit_value"]!=case["query"]:
            rec["failure_signature"]="USPTO_QUERY_BINDING_FAILED"; return rec
        inp.press("Enter")
        terminal=None
        for _ in range(40):
            page.wait_for_timeout(400)
            p=probe(page,case["query"])
            if p["control"] or p["positive"] or p["zero"]:
                terminal=p; break
        rec["terminal"]=terminal or probe(page,case["query"])
        if rec["terminal"]["control"]:
            rec["state"]="BLOCKED"; rec["failure_signature"]="USPTO_CONTROL_BLOCKED"
        elif case["expected"]=="POSITIVE" and rec["terminal"]["positive"]:
            rec["state"]="PASS"
        elif case["expected"]=="ZERO" and rec["terminal"]["zero"]:
            rec["state"]="PASS"
        else:
            rec["failure_signature"]="USPTO_NATIVE_RESULTSET_SEMANTICS_NOT_BOUND"
    except Exception as exc:
        rec["state"]="BLOCKED"; rec["failure_signature"]=f"{type(exc).__name__}:{str(exc)[:220]}"
    finally:
        page.close()
    return rec


def main():
    out={"schema":"AVER_USPTO_OFFICIAL_CANARY","official_source":True,"shadow_only":True,"candidate_queries_executed":False,"tm_decision_authorized":False,"daily7_live_gate_authorized":False,"phase_state":"USPTO_OFFICIAL_CANARY_PARTIAL","cases":[]}
    executable=os.getenv("AVER_BROWSER_EXECUTABLE") or None
    with sync_playwright() as p:
        launch={"headless":True}
        if executable: launch["executable_path"]=executable
        browser=p.chromium.launch(**launch)
        for case in CASES: out["cases"].append(run_case(browser,case))
        browser.close()
    if all(x["state"]=="PASS" for x in out["cases"]): out["phase_state"]="USPTO_SINGLE_TERM_NATIVE_SEMANTICS_PASS"
    path=Path("artifacts/uspto-official"); path.mkdir(parents=True,exist_ok=True)
    (path/"receipt.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print("phase_state=",out["phase_state"])
    for x in out["cases"]: print(x["name"],x["state"],x.get("failure_signature"),(x.get("terminal") or {}).get("count"))
    if out["phase_state"]!="USPTO_SINGLE_TERM_NATIVE_SEMANTICS_PASS": raise SystemExit("USPTO_OFFICIAL_CANARY_NOT_PASS")

if __name__=="__main__": main()
