#!/usr/bin/env python3
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from aver.resolvers import TrademarkiaResolver

CASES=[
    {"name":"QUOTED_KNOWN_POSITIVE","query":"\"JUST DO IT\"","expected":"KNOWN_POSITIVE","identifier":"50086105"},
    {"name":"QUOTED_PRODUCTION_PHRASE","query":"\"Mildly Lost, Weirdly Optimistic\"","expected":"OPAQUE_ZERO","identifier":None},
]


def main():
    out={
        "schema":"AVER_TRADEMARKIA_QUOTED_MULTIWORD_CANARY",
        "fixed_production_phrase":True,
        "phrase_replacement_forbidden":True,
        "generalization_to_arbitrary_phrase_forbidden":True,
        "daily7_candidate_queries_executed":False,
        "daily7_live_gate_authorized":False,
        "phase_state":"TRADEMARKIA_QUOTED_MULTIWORD_PARTIAL",
        "cases":[],
    }
    executable=os.getenv("AVER_BROWSER_EXECUTABLE") or None
    with sync_playwright() as p:
        launch={"headless":True}
        if executable:
            launch["executable_path"]=executable
        browser=p.chromium.launch(**launch)
        resolver=TrademarkiaResolver(browser)
        for case in CASES:
            rec=resolver.search(case["query"],case["expected"],expected_identifier=case["identifier"])
            out["cases"].append({"case":case,"resolver_receipt":rec})
        browser.close()

    pos=out["cases"][0]["resolver_receipt"]
    neg=out["cases"][1]["resolver_receipt"]
    pos_ok=(pos.get("state")=="CAPABILITY_PASS" and (pos.get("terminal_result") or {}).get("terminal")=="POSITIVE_RESULTSET" and pos.get("query_binding_attestation",{}).get("bound") is True)
    neg_ok=(neg.get("state")=="CAPABILITY_PASS" and (neg.get("terminal_result") or {}).get("terminal")=="ZERO_RESULTSET" and neg.get("query_binding_attestation",{}).get("bound") is True)
    if pos_ok and neg_ok:
        out["phase_state"]="TRADEMARKIA_QUOTED_PRODUCTION_PHRASE_ZERO_PASS"

    path=Path("artifacts/trademarkia-quoted")
    path.mkdir(parents=True,exist_ok=True)
    (path/"receipt.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print("phase_state=",out["phase_state"])
    for item in out["cases"]:
        r=item["resolver_receipt"]
        print(item["case"]["name"],r.get("state"),r.get("failure_signature"),(r.get("terminal_result") or {}).get("terminal"),(r.get("terminal_result") or {}).get("reported_total"))
    if out["phase_state"]!="TRADEMARKIA_QUOTED_PRODUCTION_PHRASE_ZERO_PASS":
        raise SystemExit("TRADEMARKIA_QUOTED_CANARY_NOT_PASS")

if __name__=="__main__":
    main()
