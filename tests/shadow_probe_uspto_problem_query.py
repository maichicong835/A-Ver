#!/usr/bin/env python3
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from aver.uspto_fieldtag_direct_canary import run_case

CASES=[
    {"name":"W_SECONDARY_CORE_EXACT","query":"CM:\"CREATING SPREADSHEET\"","expected":"ZERO"},
    {"name":"W_SECONDARY_CORE_EXPANDED_PARTIAL","query":"CM:(/.*creating.*/ AND /.*spreadsheet.*/)","expected":"ZERO"},
    {"name":"W_PRIMARY_CORE_EXPANDED_PARTIAL_CONTROL","query":"CM:(/.*silently.*/ AND /.*creating.*/ AND /.*spreadsheet.*/)","expected":"ZERO"},
]


def summarize(rec):
    t=rec.get("terminal") or {}
    if t.get("positive") is True:
        outcome="POSITIVE"
    elif t.get("native_zero") is True:
        outcome="NEGATIVE"
    elif t.get("control_blocked") is True:
        outcome="CONTROL_BLOCKED"
    else:
        outcome="UNRESOLVED"
    return {
        "name":rec.get("name"),
        "query":rec.get("query"),
        "state":rec.get("state"),
        "failure_signature":rec.get("failure_signature"),
        "outcome":outcome,
        "count":t.get("count"),
        "positive":t.get("positive"),
        "native_zero":t.get("native_zero"),
        "control_blocked":t.get("control_blocked"),
        "query_visible":t.get("query_visible"),
        "final_url":t.get("final_url"),
        "body_excerpt":t.get("body_excerpt") or rec.get("body_excerpt"),
        "visible_inputs":rec.get("visible_inputs"),
    }


def main():
    out={
        "schema":"AVER_SHADOW_USPTO_PROBLEM_QUERY_PROBE",
        "engine_commit_sha":os.getenv("GITHUB_SHA") or os.getenv("AVER_ENGINE_COMMIT_SHA"),
        "candidate":"I'M SILENTLY CREATING A SPREADSHEET FOR THAT",
        "purpose":"isolate whether the second expanded-partial query itself is operationally pathological on a fresh runner",
        "tm_decision_authorized":False,
        "cases":[],
    }
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        for case in CASES:
            out["cases"].append(summarize(run_case(browser,case)))
        browser.close()
    path=Path("artifacts/problem-query")
    path.mkdir(parents=True,exist_ok=True)
    (path/"receipt.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    for c in out["cases"]:
        print("USPTO_PROBLEM_QUERY",c["name"],c["outcome"],c["state"],c["failure_signature"],c["count"],c["final_url"])

if __name__=="__main__":
    main()
