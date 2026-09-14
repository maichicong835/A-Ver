#!/usr/bin/env python3
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from aver.tsdr_targeted_canary import run_case

CASE={
    "candidate_key":"w-silently-creating-spreadsheet",
    "serial":"77348348",
    "mark":"COMPUTER SOFTWARE APPLICATION/TOOL BASED ON MS EXCEL",
    "shared_component":"SPREADSHEET",
}


def main():
    out={
        "schema":"AVER_SHADOW_TSDR_W_RECORD_PROBE",
        "engine_commit_sha":os.getenv("GITHUB_SHA") or os.getenv("AVER_ENGINE_COMMIT_SHA"),
        "official_source":True,
        "known_identifier_only":True,
        "tm_decision_authorized":False,
        "case":None,
    }
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        out["case"]=run_case(browser,CASE)
        browser.close()
    path=Path("artifacts/tsdr-w-record")
    path.mkdir(parents=True,exist_ok=True)
    (path/"receipt.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    c=out["case"]
    print("TSDR_W_RECORD",c.get("serial"),c.get("state"),c.get("failure_signature"),c.get("status_tokens"),c.get("retry_count"))

if __name__=="__main__":
    main()
