#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

URL="https://tmsearch.uspto.gov/"
CASES=[
    {"name":"KNOWN_POSITIVE_SINGLE_TERM","term":"NIKE","field_query":"CM:NIKE","expected":"POSITIVE"},
    {"name":"OPAQUE_ZERO_SINGLE_TERM","term":"QZXJVMRKPLN91372","field_query":"CM:QZXJVMRKPLN91372","expected":"ZERO"},
]


def body_text(page):
    try:
        return re.sub(r"\s+"," ",page.locator("body").inner_text(timeout=5000)).strip()
    except Exception:
        return ""


def visible_ui(page):
    out={"body_excerpt":body_text(page)[:2600],"buttons":[],"inputs":[]}
    try:
        loc=page.locator("button")
        for i in range(min(loc.count(),40)):
            el=loc.nth(i)
            if el.is_visible(): out["buttons"].append((el.inner_text() or "").strip()[:160])
    except Exception: pass
    try:
        loc=page.locator("input,textarea")
        for i in range(min(loc.count(),40)):
            el=loc.nth(i)
            if el.is_visible(): out["inputs"].append({"placeholder":el.get_attribute("placeholder") or "","aria_label":el.get_attribute("aria-label") or "","type":el.get_attribute("type") or ""})
    except Exception: pass
    return out


def select_field_tag_mode(page):
    # If the field-tag search input is already visible, the correct mode is active.
    for selector in ["input[placeholder*='field tag' i]","textarea[placeholder*='field tag' i]","input[placeholder*='Search using field tags' i]"]:
        try:
            loc=page.locator(selector)
            if loc.count() and loc.first.is_visible():
                return {"selected":True,"method":"field_tag_input_already_visible","selector":selector}
        except Exception: pass
    for opener in ["button:has-text('Field tag and Search builder')","text='Field tag and Search builder'","button:has-text('General search')"]:
        try:
            loc=page.locator(opener)
            if not (loc.count() and loc.first.is_visible()): continue
            loc.first.click(); page.wait_for_timeout(300)
            # Some builds expose the option only after opening General search.
            for option in ["text='Field tag and Search builder'","[role='option']:has-text('Field tag and Search builder')","button:has-text('Field tag and Search builder')"]:
                op=page.locator(option)
                for j in range(min(op.count(),10)):
                    if op.nth(j).is_visible():
                        try: op.nth(j).click(); page.wait_for_timeout(350)
                        except Exception: pass
                        for field_input in ["input[placeholder*='field tag' i]","textarea[placeholder*='field tag' i]","input[placeholder*='Search using field tags' i]"]:
                            fi=page.locator(field_input)
                            if fi.count() and fi.first.is_visible():
                                return {"selected":True,"method":f"{opener}->{option}","selector":field_input}
        except Exception: pass
    return {"selected":False,"ui":visible_ui(page)}


def choose_field_input(page):
    candidates=[]
    for selector in ["input","textarea"]:
        try:
            loc=page.locator(selector)
            for i in range(min(loc.count(),40)):
                el=loc.nth(i)
                if not el.is_visible(): continue
                ph=el.get_attribute("placeholder") or ""
                aria=el.get_attribute("aria-label") or ""
                desc={"selector":selector,"index":i,"placeholder":ph,"aria_label":aria,"type":el.get_attribute("type") or ""}
                candidates.append(desc)
                blob=(ph+" "+aria).lower()
                if "field tag" in blob or "search using" in blob:
                    return el,candidates
        except Exception: pass
    return None,candidates


def probe(page,term,field_query):
    body=body_text(page)
    lower=body.lower()
    count=None
    m=re.search(r"([\d,]+)\s+results?\s+for",body,re.I)
    if m: count=int(m.group(1).replace(",",""))
    control=any(x in lower for x in ("captcha","verify you are human","are you a robot","access denied"))
    zero=(count==0) or "no results found" in lower
    positive=(count is not None and count>0)
    return {"count":count,"positive":positive,"zero":zero,"control":control,"term_visible":term.lower() in lower,"field_query_visible":field_query.lower() in lower,"body_excerpt":body[:3500],"final_url":page.url}


def run_case(browser,case):
    page=browser.new_page(viewport={"width":1440,"height":1000})
    rec={**case,"state":"UNPROVEN","failure_signature":None}
    try:
        page.goto(URL,wait_until="domcontentloaded",timeout=30000); page.wait_for_timeout(1200)
        rec["field_tag_mode"]=select_field_tag_mode(page)
        if not rec["field_tag_mode"].get("selected"):
            rec["failure_signature"]="USPTO_FIELD_TAG_MODE_NOT_BOUND"; return rec
        inp,candidates=choose_field_input(page); rec["input_candidates"]=candidates
        if inp is None:
            rec["failure_signature"]="USPTO_FIELD_TAG_INPUT_NOT_FOUND"; rec["ui"]=visible_ui(page); return rec
        inp.fill(case["field_query"]); page.wait_for_timeout(300)
        rec["pre_submit_value"]=inp.input_value(timeout=1500)
        if rec["pre_submit_value"]!=case["field_query"]:
            rec["failure_signature"]="USPTO_QUERY_BINDING_FAILED"; return rec
        inp.press("Enter")
        terminal=None
        for _ in range(45):
            page.wait_for_timeout(400)
            p=probe(page,case["term"],case["field_query"])
            if p["control"] or p["positive"] or p["zero"]:
                terminal=p; break
        rec["terminal"]=terminal or probe(page,case["term"],case["field_query"])
        if rec["terminal"]["control"]:
            rec["state"]="BLOCKED"; rec["failure_signature"]="USPTO_CONTROL_BLOCKED"
        elif case["expected"]=="POSITIVE" and rec["terminal"]["positive"]:
            rec["state"]="PASS"
        elif case["expected"]=="ZERO" and rec["terminal"]["zero"]:
            rec["state"]="PASS"
        else:
            rec["failure_signature"]="USPTO_NATIVE_RESULTSET_SEMANTICS_NOT_BOUND"
    except Exception as exc:
        rec["state"]="BLOCKED"; rec["failure_signature"]=f"{type(exc).__name__}:{str(exc)[:220]}"; rec["ui"]=visible_ui(page)
    finally:
        page.close()
    return rec


def main():
    out={"schema":"AVER_USPTO_OFFICIAL_CANARY","official_source":True,"shadow_only":True,"candidate_queries_executed":False,"tm_decision_authorized":False,"daily7_live_gate_authorized":False,"phase_state":"USPTO_OFFICIAL_CANARY_PARTIAL","repair_iteration":1,"cases":[]}
    executable=os.getenv("AVER_BROWSER_EXECUTABLE") or None
    with sync_playwright() as p:
        launch={"headless":True}
        if executable: launch["executable_path"]=executable
        browser=p.chromium.launch(**launch)
        for case in CASES: out["cases"].append(run_case(browser,case))
        browser.close()
    if all(x["state"]=="PASS" for x in out["cases"]): out["phase_state"]="USPTO_FIELD_TAG_SINGLE_TERM_NATIVE_SEMANTICS_PASS"
    path=Path("artifacts/uspto-official"); path.mkdir(parents=True,exist_ok=True)
    (path/"receipt.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print("phase_state=",out["phase_state"])
    for x in out["cases"]: print(x["name"],x["state"],x.get("failure_signature"),(x.get("terminal") or {}).get("count"))
    if out["phase_state"]!="USPTO_FIELD_TAG_SINGLE_TERM_NATIVE_SEMANTICS_PASS": raise SystemExit("USPTO_OFFICIAL_CANARY_NOT_PASS_AFTER_ONE_CAUSAL_REPAIR")

if __name__=="__main__": main()
