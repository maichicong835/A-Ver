#!/usr/bin/env python3
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from aver.uspto_fieldtag_direct_canary import run_case

CASES = [
    {
        "candidate_key": "h-spreadsheets-life-make-sense",
        "query": 'CM:"MAYBE WITH ENOUGH SPREADSHEETS LIFE WILL MAKE SENSE"',
        "expected": "ZERO",
    },
    {
        "candidate_key": "w-silently-creating-spreadsheet",
        "query": 'CM:"I\'M SILENTLY CREATING A SPREADSHEET FOR THAT"',
        "expected": "ZERO",
    },
]

out = {
    "schema": "AVER_SHADOW_USPTO_FRESH_FIRST_PROBE",
    "purpose": "Distinguish phrase-specific incompatibility from session/order/rate-dependent USPTO input-binding failure",
    "tm_decision_authorized": False,
    "production_pin_change_authorized": False,
    "cases": [],
}

with sync_playwright() as p:
    for case in CASES:
        browser = p.chromium.launch(headless=True)
        rec = run_case(browser, {
            "name": "FRESH_FIRST:" + case["candidate_key"],
            "query": case["query"],
            "expected": case["expected"],
        })
        browser.close()
        rec["candidate_key"] = case["candidate_key"]
        out["cases"].append(rec)
        terminal = rec.get("terminal") or {}
        print(case["candidate_key"], rec.get("state"), rec.get("failure_signature"), terminal.get("count"), rec.get("page_url") or terminal.get("final_url"), rec.get("page_title"))

path = Path("artifacts/capability-release/uspto-fresh-first-probe.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
print("AVER_SHADOW_USPTO_FRESH_FIRST_PROBE_COMPLETE")
