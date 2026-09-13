#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

URL="https://tmsearch.uspto.gov/"
CASES=[
    {"name":"KNOWN_POSITIVE_MULTIWORD_EXACT","query":"CM:\"JUST DO IT\"","expected":"POSITIVE"},
    {"name":"OPAQUE_MULTIWORD_EXACT_ZERO","query":"CM:\"QZXJVMRKPLNX VQTKRMNZXJQW\"","expected":"ZERO"},
]


def body_text(page):
    try:
        return re.sub(r"\s+"," ",page.locator("body").inner_text(timeout=5000)).strip()
    except Exception:
        return ""


def visible_inputs(page):
    rows=[]
    loc=page.locator("input,textarea")
    for i in range(min(loc.count(),40)):
        el=loc.nth(i)
        try:
            if not el.is_visible():
                continue
            rows.append({
                "index":i,
                "tag":el.evaluate("e=>e.tagName"),
                "type":el.get_attribute("type") or "",
                "placeholder":el.get_attribute("placeholder") or "",
                "aria_label":el.get_attribute("aria-label") or "",
            })
        except Exception:
            pass
    return rows


def choose_public_search_input(page):
    loc=page.locator("input,textarea")
    ranked=[]
    for i in range(min(loc.count(),40)):
        el=loc.nth(i)
        try:
            if not el.is_visible():
                continue
            ph=el.get_attribute("placeholder") or ""
            aria=el.get_attribute("aria-label") or ""
            typ=(el.get_attribute("type") or "").lower()
            blob=(ph+" "+aria).lower()
            score=0
            if "search" in blob: score+=3
            if "mark" in blob: score+=2
            if typ in ("search","text",""): score+=1
            ranked.append((score,i,el,ph,aria,typ))
        except Exception:
            pass
    ranked.sort(key=lambda x:(-x[0],x[1]))
    if not ranked or ranked[0][0] < 3:
        return None, visible_inputs(page)
    return ranked[0][2], visible_inputs(page)


def probe(page,query):
    body=body_text(page)
    low=body.lower()
    count=None
    patterns=[
        r"([\d,]+)\s+results?\s+for",
        r"([\d,]+)\s+results?\b",
        r"showing\s+[\d,]+(?:\s*[-–]\s*[\d,]+)?\s+of\s+([\d,]+)",
    ]
    for pat in patterns:
        m=re.search(pat,body,re.I)
        if m:
            count=int(m.group(1).replace(",","")); break
    control=any(x in low for x in ("captcha","verify you are human","are you a robot","access denied"))
    native_zero=(count==0) or any(x in low for x in ("no results found","0 results","no trademarks found"))
    positive=(count is not None and count>0)
    return {
        "count":count,
        "positive":positive,
        "native_zero":native_zero,
        "control_blocked":control,
        "query_visible":query.lower() in low,
        "final_url":page.url,
        "body_excerpt":body[:4200],
    }


def run_case(browser,case):
    page=browser.new_page(viewport={"width":1440,"height":1000})
    rec={**case,"state":"UNPROVEN","failure_signature":None}
    try:
        page.goto(URL,wait_until="domcontentloaded",timeout=30000)
        page.wait_for_timeout(1200)
        inp,inputs=choose_public_search_input(page)
        rec["visible_inputs"]=inputs
        if inp is None:
            rec["failure_signature"]="USPTO_PUBLIC_SEARCH_INPUT_NOT_BOUND"
            return rec
        rec["chosen_input"]={
            "placeholder":inp.get_attribute("placeholder") or "",
            "aria_label":inp.get_attribute("aria-label") or "",
            "type":inp.get_attribute("type") or "",
        }
        inp.fill(case["query"])
        page.wait_for_timeout(250)
        rec["pre_submit_value_1"]=inp.input_value(timeout=1500)
        page.wait_for_timeout(250)
        rec["pre_submit_value_2"]=inp.input_value(timeout=1500)
        if rec["pre_submit_value_1"]!=case["query"] or rec["pre_submit_value_2"]!=case["query"]:
            rec["failure_signature"]="USPTO_DIRECT_FIELD_TAG_QUERY_BINDING_UNSTABLE"
            return rec
        inp.press("Enter")
        terminal=None
        for _ in range(50):
            page.wait_for_timeout(400)
            p=probe(page,case["query"])
            if p["control_blocked"] or p["positive"] or p["native_zero"]:
                terminal=p; break
        rec["terminal"]=terminal or probe(page,case["query"])
        t=rec["terminal"]
        if t["control_blocked"]:
            rec["state"]="HOLD_CAPABILITY"
            rec["failure_signature"]="USPTO_CONTROL_BLOCKED"
        elif case["expected"]=="POSITIVE" and t["positive"]:
            rec["state"]="PASS"
        elif case["expected"]=="ZERO" and t["native_zero"]:
            rec["state"]="PASS"
        else:
            rec["failure_signature"]="USPTO_DIRECT_FIELD_TAG_NATIVE_SEMANTICS_NOT_BOUND"
    except Exception as exc:
        rec["state"]="HOLD_CAPABILITY"
        rec["failure_signature"]=f"{type(exc).__name__}:{str(exc)[:240]}"
        rec["body_excerpt"]=body_text(page)[:2400]
    finally:
        page.close()
    return rec


def main():
    out={
        "schema":"AVER_USPTO_DIRECT_FIELDTAG_CANARY",
        "official_source":True,
        "strategy":"DIRECT_FIELD_TAG_QUERY_IN_PUBLIC_SEARCH_INPUT",
        "same_strategy_as_prior_mode_binding_cycle":False,
        "fixed_canaries_only":True,
        "daily7_candidate_queries_executed":False,
        "tm_decision_authorized":False,
        "phase_state":"USPTO_DIRECT_FIELDTAG_PARTIAL",
        "cases":[],
    }
    executable=os.getenv("AVER_BROWSER_EXECUTABLE") or None
    with sync_playwright() as p:
        launch={"headless":True}
        if executable: launch["executable_path"]=executable
        browser=p.chromium.launch(**launch)
        for case in CASES:
            out["cases"].append(run_case(browser,case))
        browser.close()
    if all(c["state"]=="PASS" for c in out["cases"]):
        out["phase_state"]="USPTO_DIRECT_FIELDTAG_MULTIWORD_SEMANTICS_PASS"
    path=Path("artifacts/uspto-fieldtag")
    path.mkdir(parents=True,exist_ok=True)
    (path/"receipt.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print("phase_state=",out["phase_state"])
    for c in out["cases"]:
        print(c["name"],c["state"],c.get("failure_signature"),(c.get("terminal") or {}).get("count"))
    if out["phase_state"]!="USPTO_DIRECT_FIELDTAG_MULTIWORD_SEMANTICS_PASS":
        raise SystemExit("USPTO_DIRECT_FIELDTAG_CANARY_NOT_PASS")

if __name__=="__main__":
    main()
