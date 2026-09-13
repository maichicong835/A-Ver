#!/usr/bin/env python3
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
from aver.resolvers import TrademarkiaResolver

CASES = [
    {
        "name": "KNOWN_POSITIVE_MULTIWORD",
        "query": "JUST DO IT",
        "expected_kind": "KNOWN_POSITIVE",
        "expected_identifier": "50086105",
    },
    {
        "name": "OPAQUE_MULTIWORD_ZERO_FIXED_CANARY",
        "query": "QZXJVMRKPLNX VQTKRMNZXJQW",
        "expected_kind": "OPAQUE_ZERO",
        "expected_identifier": None,
    },
]


def main():
    out = {
        "schema": "AVER_TRADEMARKIA_MULTIWORD_FIXED_CANARY",
        "shadow_only": True,
        "fixed_canary_only": True,
        "generalization_to_arbitrary_multiword_exact_negative_forbidden": True,
        "candidate_queries_executed": False,
        "tm_decision_authorized": False,
        "daily7_live_gate_authorized": False,
        "phase_state": "TRADEMARKIA_MULTIWORD_FIXED_CANARY_PARTIAL",
        "cases": [],
    }
    executable = os.getenv("AVER_BROWSER_EXECUTABLE") or None
    with sync_playwright() as p:
        launch = {"headless": True}
        if executable:
            launch["executable_path"] = executable
        browser = p.chromium.launch(**launch)
        resolver = TrademarkiaResolver(browser)
        for case in CASES:
            rec = resolver.search(
                case["query"],
                case["expected_kind"],
                expected_identifier=case["expected_identifier"],
            )
            out["cases"].append({"case": case, "resolver_receipt": rec})
        browser.close()

    positive = out["cases"][0]["resolver_receipt"]
    zero = out["cases"][1]["resolver_receipt"]
    positive_ok = (
        positive.get("state") == "CAPABILITY_PASS"
        and (positive.get("terminal_result") or {}).get("terminal") == "POSITIVE_RESULTSET"
        and positive.get("query_binding_attestation", {}).get("bound") is True
    )
    zero_ok = (
        zero.get("state") == "CAPABILITY_PASS"
        and (zero.get("terminal_result") or {}).get("terminal") == "ZERO_RESULTSET"
        and zero.get("query_binding_attestation", {}).get("bound") is True
    )
    if positive_ok and zero_ok:
        out["phase_state"] = "TRADEMARKIA_MULTIWORD_FIXED_CANARY_PASS"

    path = Path("artifacts/trademarkia-multiword")
    path.mkdir(parents=True, exist_ok=True)
    (path / "receipt.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    print("phase_state=", out["phase_state"])
    for item in out["cases"]:
        r = item["resolver_receipt"]
        print(item["case"]["name"], r.get("state"), r.get("failure_signature"), (r.get("terminal_result") or {}).get("terminal"))
    if out["phase_state"] != "TRADEMARKIA_MULTIWORD_FIXED_CANARY_PASS":
        raise SystemExit("TRADEMARKIA_MULTIWORD_FIXED_CANARY_NOT_PASS")


if __name__ == "__main__":
    main()
