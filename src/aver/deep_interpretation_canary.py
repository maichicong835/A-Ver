#!/usr/bin/env python3
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

from aver.record_interpretation import bind_record_anchor, discover_record_anchors_from_page
from aver.resolvers import TrademarkiaResolver

CANARIES = [
    {
        "candidate_key": "nursing-school-hard-but-damn",
        "wording": "I KNOW THEY SAID NURSING SCHOOL WAS HARD, BUT DAMN",
        "expected_mark": "NURSING SCHOOL JEWELS",
        "expected_serial": "90319838",
        "expected_class": "016"
    },
    {
        "candidate_key": "powered-by-yarn-and-chaos",
        "wording": "POWERED BY YARN AND CHAOS",
        "expected_mark": "CHAOS BY ELSIE",
        "expected_serial": "90072046",
        "expected_class": "018"
    }
]


def main():
    output = {
        "schema": "AVER_DEEP_INTERPRETATION_CANARY_RECEIPT",
        "shadow_only": True,
        "candidate_breadth_expanded": False,
        "tm_decision_authorized": False,
        "daily7_live_gate_authorized": False,
        "canaries": [],
        "phase_state": "DEEP_RECORD_DISCOVERY_PARTIAL"
    }
    executable = os.getenv("AVER_BROWSER_EXECUTABLE") or None
    with sync_playwright() as p:
        launch = {"headless": True}
        if executable:
            launch["executable_path"] = executable
        browser = p.chromium.launch(**launch)
        resolver = TrademarkiaResolver(browser)
        for c in CANARIES:
            rec = resolver.search(c["wording"], "FUZZY_RECALL", post_terminal_observer=lambda page, terminal: discover_record_anchors_from_page(page, limit=12))
            anchors = rec.get("post_terminal_observation") or []
            target = next((x for x in anchors if x.get("identifier") == c["expected_serial"]), None)
            bound = None
            if target:
                bound = bind_record_anchor(target.get("container_text", ""), c["expected_mark"], c["expected_serial"], c["expected_class"])
            passed = bool(
                rec.get("state") == "CAPABILITY_PASS"
                and (rec.get("terminal_result") or {}).get("terminal") == "POSITIVE_RESULTSET"
                and rec.get("post_terminal_observer_state") == "OBSERVED"
                and target
                and bound
                and bound.get("bound") is True
            )
            output["canaries"].append({
                **c,
                "resolver_state": rec.get("state"),
                "terminal": (rec.get("terminal_result") or {}).get("terminal"),
                "observer_state": rec.get("post_terminal_observer_state"),
                "anchor_count": len(anchors),
                "expected_anchor_found": target is not None,
                "expected_anchor": target,
                "record_binding": bound,
                "pass": passed,
                "failure_signature": rec.get("failure_signature"),
                "observer_error": rec.get("post_terminal_observer_error")
            })
        browser.close()

    if len(output["canaries"]) == 2 and all(x["pass"] for x in output["canaries"]):
        output["phase_state"] = "DEEP_RECORD_DISCOVERY_PASS"

    out = Path("artifacts/deep-interpretation")
    out.mkdir(parents=True, exist_ok=True)
    (out / "receipt.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print("phase_state=", output["phase_state"])
    for x in output["canaries"]:
        print(x["candidate_key"], "anchors=", x["anchor_count"], "expected=", x["expected_anchor_found"], "bound=", bool((x["record_binding"] or {}).get("bound")))
    if output["phase_state"] != "DEEP_RECORD_DISCOVERY_PASS":
        raise SystemExit("DEEP_RECORD_DISCOVERY_NOT_PASS")


if __name__ == "__main__":
    main()
