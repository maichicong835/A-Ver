#!/usr/bin/env python3
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from aver.query_plan import build_query_plan, normalize_wording
from aver.uspto_fieldtag_direct_canary import run_case

PHRASES = [
    ("h-spreadsheets-life-make-sense", "MAYBE WITH ENOUGH SPREADSHEETS LIFE WILL MAKE SENSE"),
    ("w-silently-creating-spreadsheet", "I'M SILENTLY CREATING A SPREADSHEET FOR THAT"),
]

def exact_query(value):
    return 'CM:"' + value.replace('"', '').strip() + '"'

out = {
    "schema": "AVER_SHADOW_USPTO_LONG_PHRASE_PROBE",
    "tm_decision_authorized": False,
    "production_pin_change_authorized": False,
    "cases": [],
}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for candidate_key, phrase in PHRASES:
        plan = build_query_plan(phrase, [])
        probes = [
            ("EXACT", phrase),
            ("NORMALIZED_EXACT", normalize_wording(phrase)),
        ]
        probes += [("CORE_DOMINANT_TOKEN", core) for core in plan["CORE_DOMINANT_TOKEN"]["queries"]]
        for dimension, value in probes:
            case = {
                "name": f"{candidate_key}:{dimension}:{value}",
                "query": exact_query(value),
                "expected": "ZERO",
            }
            rec = run_case(browser, case)
            rec["candidate_key"] = candidate_key
            rec["dimension"] = dimension
            out["cases"].append(rec)
            terminal = rec.get("terminal") or {}
            print(candidate_key, dimension, rec.get("state"), rec.get("failure_signature"), terminal.get("count"), terminal.get("query_visible"), terminal.get("final_url"))
    browser.close()

path = Path("artifacts/capability-release/uspto-long-phrase-probe.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
print("AVER_SHADOW_USPTO_LONG_PHRASE_PROBE_COMPLETE")
