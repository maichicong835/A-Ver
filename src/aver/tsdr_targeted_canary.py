#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

CASES=[
    {"candidate_key":"nursing-school-hard-but-damn","serial":"90319838","mark":"NURSING SCHOOL JEWELS","shared_component":"NURSING SCHOOL"},
    {"candidate_key":"powered-by-yarn-and-chaos","serial":"88678935","mark":"YARN","shared_component":"YARN"},
]


def compact(value):
    return re.sub(r"\s+"," ",value or "").strip()


def run_case(browser,c):
    url=f"https://tsdr.uspto.gov/#caseNumber={c['serial']}&caseSearchType=US_APPLICATION&caseType=DEFAULT&searchType=statusSearch"
    page=browser.new_page(viewport={"width":1440,"height":1100})
    rec={**c,"url":url,"state":"UNPROVEN","failure_signature":None}
    try:
        page.goto(url,wait_until="domcontentloaded",timeout=30000)
        body=""
        for _ in range(30):
            page.wait_for_timeout(500)
            try: body=compact(page.locator("body").inner_text(timeout=3000))
            except Exception: body=""
            if c["serial"] in body and c["mark"].lower() in body.lower(): break
        lower=body.lower()
        control=any(x in lower for x in ("captcha","verify you are human","are you a robot","access denied"))
        serial_seen=c["serial"] in body
        mark_seen=c["mark"].lower() in lower
        status_tokens=[x for x in ["LIVE","REGISTERED","PENDING","DEAD","CANCELLED","ABANDONED"] if x.lower() in lower]
        disclaimer_excerpt=None
        # Capture a bounded context around disclaimer wording if present.
        idx=lower.find("disclaim")
        if idx>=0: disclaimer_excerpt=body[max(0,idx-250):idx+900]
        shared_seen=c["shared_component"].lower() in lower
        rec.update({
            "serial_seen":serial_seen,
            "mark_seen":mark_seen,
            "status_tokens":status_tokens,
            "shared_component_seen":shared_seen,
            "disclaimer_context":disclaimer_excerpt,
            "final_url":page.url,
            "body_excerpt":body[:5000],
            "control_marker":control,
        })
        if control:
            rec["state"]="BLOCKED"; rec["failure_signature"]="TSDR_CONTROL_BLOCKED"
        elif serial_seen and mark_seen and status_tokens:
            rec["state"]="PASS"
        else:
            rec["failure_signature"]="TSDR_RECORD_FIELDS_NOT_MACHINE_BOUND"
    except Exception as exc:
        rec["state"]="BLOCKED"; rec["failure_signature"]=f"{type(exc).__name__}:{str(exc)[:220]}"
    finally:
        page.close()
    return rec


def main():
    out={"schema":"AVER_TSDR_TARGETED_CANARY","official_source":True,"known_identifiers_only":True,"candidate_breadth_expanded":False,"tm_decision_authorized":False,"daily7_live_gate_authorized":False,"phase_state":"TSDR_TARGETED_PARTIAL","cases":[]}
    executable=os.getenv("AVER_BROWSER_EXECUTABLE") or None
    with sync_playwright() as p:
        launch={"headless":True}
        if executable: launch["executable_path"]=executable
        browser=p.chromium.launch(**launch)
        for c in CASES: out["cases"].append(run_case(browser,c))
        browser.close()
    if all(x["state"]=="PASS" for x in out["cases"]): out["phase_state"]="TSDR_TARGETED_RECORD_PASS"
    path=Path("artifacts/tsdr-targeted"); path.mkdir(parents=True,exist_ok=True)
    (path/"receipt.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print("phase_state=",out["phase_state"])
    for x in out["cases"]: print(x["serial"],x["state"],x.get("failure_signature"),bool(x.get("disclaimer_context")))
    if out["phase_state"]!="TSDR_TARGETED_RECORD_PASS": raise SystemExit("TSDR_TARGETED_RECORD_NOT_PASS")

if __name__=="__main__": main()
