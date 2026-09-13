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


def observe_case(browser,c,attempt):
    url=f"https://tsdr.uspto.gov/#caseNumber={c['serial']}&caseSearchType=US_APPLICATION&caseType=DEFAULT&searchType=statusSearch"
    page=browser.new_page(viewport={"width":1440,"height":1100})
    obs={"attempt":attempt,"url":url}
    try:
        page.goto(url,wait_until="domcontentloaded",timeout=30000)
        body=""
        for _ in range(30):
            page.wait_for_timeout(500)
            try: body=compact(page.locator("body").inner_text(timeout=3000))
            except Exception: body=""
            lower=body.lower()
            if c["serial"] in body and c["mark"].lower() in lower: break
            if "system was unable to perform your search" in lower: break
        lower=body.lower()
        control=any(x in lower for x in ("captcha","verify you are human","are you a robot","access denied"))
        serial_seen=c["serial"] in body
        mark_seen=c["mark"].lower() in lower
        status_tokens=[x for x in ["LIVE","REGISTERED","PENDING","DEAD","CANCELLED","ABANDONED"] if x.lower() in lower]
        native_search_failure="system was unable to perform your search" in lower
        disclaimer_excerpt=None
        idx=lower.find("disclaim")
        if idx>=0: disclaimer_excerpt=body[max(0,idx-250):idx+900]
        obs.update({
            "serial_seen":serial_seen,
            "mark_seen":mark_seen,
            "status_tokens":status_tokens,
            "shared_component_seen":c["shared_component"].lower() in lower,
            "disclaimer_context":disclaimer_excerpt,
            "native_search_failure":native_search_failure,
            "final_url":page.url,
            "body_excerpt":body[:5000],
            "control_marker":control,
        })
    except Exception as exc:
        obs.update({"exception":f"{type(exc).__name__}:{str(exc)[:220]}","native_search_failure":False,"control_marker":False})
    finally:
        page.close()
    return obs


def run_case(browser,c):
    rec={**c,"state":"UNPROVEN","failure_signature":None,"attempts":[]}
    max_attempts=2
    for attempt in range(1,max_attempts+1):
        obs=observe_case(browser,c,attempt)
        rec["attempts"].append(obs)
        if obs.get("control_marker"):
            rec["state"]="BLOCKED"; rec["failure_signature"]="TSDR_CONTROL_BLOCKED"; break
        if obs.get("serial_seen") and obs.get("mark_seen") and obs.get("status_tokens"):
            rec.update({k:obs.get(k) for k in ["url","serial_seen","mark_seen","status_tokens","shared_component_seen","disclaimer_context","final_url","body_excerpt","control_marker"]})
            rec["state"]="PASS"; rec["failure_signature"]=None; break
        # One and only one retry is allowed for the native transient search failure.
        if obs.get("native_search_failure") and attempt < max_attempts:
            continue
        if obs.get("exception"):
            rec["failure_signature"]=obs["exception"]
        elif obs.get("native_search_failure"):
            rec["failure_signature"]="TSDR_NATIVE_SEARCH_FAILURE_AFTER_ONE_RETRY"
        else:
            rec["failure_signature"]="TSDR_RECORD_FIELDS_NOT_MACHINE_BOUND"
        break
    rec["retry_count"]=max(0,len(rec["attempts"])-1)
    rec["retry_policy"]="ONE_RETRY_ONLY_FOR_NATIVE_SYSTEM_UNABLE_TO_PERFORM_SEARCH"
    return rec


def main():
    out={"schema":"AVER_TSDR_TARGETED_CANARY","official_source":True,"known_identifiers_only":True,"candidate_breadth_expanded":False,"tm_decision_authorized":False,"daily7_live_gate_authorized":False,"phase_state":"TSDR_TARGETED_PARTIAL","bounded_retry_policy":"MAX_ONE_RETRY_ON_NATIVE_SEARCH_FAILURE","cases":[]}
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
    for x in out["cases"]: print(x["serial"],x["state"],x.get("failure_signature"),"retry_count=",x.get("retry_count"),"disclaimer=",bool(x.get("disclaimer_context")))
    if out["phase_state"]!="TSDR_TARGETED_RECORD_PASS": raise SystemExit("TSDR_TARGETED_RECORD_NOT_PASS_AFTER_BOUNDED_RETRY")

if __name__=="__main__": main()
