#!/usr/bin/env python3
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from resolvers import TMHuntResolver, TrademarkiaResolver

ENGINE_VERSION = "0.1.0"
HARNESS_REVISION = "a4.3-query-binding-stability"
PHASE = "A4_DECLARED_CAPABILITY_REPEATABILITY"
OUT = Path("artifacts/a4")
OUT.mkdir(parents=True, exist_ok=True)
OPAQUE = "QZXJVMRKPLN91372"


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    from playwright.sync_api import sync_playwright

    started = now()
    executable = os.getenv("AVER_BROWSER_EXECUTABLE") or None
    with sync_playwright() as p:
        launch = {"headless": True}
        if executable:
            launch["executable_path"] = executable
        browser = p.chromium.launch(**launch)
        tmhunt = TMHuntResolver(browser)
        trademarkia = TrademarkiaResolver(browser)
        records = [
            tmhunt.query("EXACT", "NIKE", "POSITIVE"),
            tmhunt.query("PARTIAL", "NIKE", "POSITIVE"),
            tmhunt.query("EXACT", OPAQUE, "ZERO"),
            trademarkia.search("JUST DO IT", "KNOWN_POSITIVE"),
            trademarkia.bind_known_record("50086105"),
            trademarkia.search(OPAQUE, "OPAQUE_ZERO"),
            trademarkia.search("AVER QZXJ KESTREL 91372", "FUZZY_RECALL"),
        ]
        browser.close()

    tmhunt_records = [r for r in records if r["resolver"] == "TMHUNT"]
    trademarkia_records = [r for r in records if r["resolver"] == "TRADEMARKIA"]
    resolver_states = {
        "TMHUNT_DECLARED_PROFILE": "PASS" if all(r["state"] == "CAPABILITY_PASS" for r in tmhunt_records) else "PARTIAL",
        "TRADEMARKIA_DECLARED_PROFILE": "PASS" if all(r["state"] == "CAPABILITY_PASS" for r in trademarkia_records) else "PARTIAL",
    }
    phase_state = "A4_DECLARED_PROFILE_PASS" if all(v == "PASS" for v in resolver_states.values()) else "A4_DECLARED_PROFILE_PARTIAL"

    receipt = {
        "schema": "AVER_ACCEPTANCE_RECEIPT",
        "engine_version": ENGINE_VERSION,
        "harness_revision": HARNESS_REVISION,
        "mode": "ACCEPTANCE_ONLY",
        "phase": PHASE,
        "authority": {
            "repository": os.getenv("GITHUB_REPOSITORY", "UNKNOWN"),
            "commit_sha": os.getenv("GITHUB_SHA", "UNKNOWN"),
            "workflow_run_id": os.getenv("GITHUB_RUN_ID", "UNKNOWN"),
            "workflow_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT", "UNKNOWN"),
            "ref": os.getenv("GITHUB_REF", "UNKNOWN"),
        },
        "browser_executable": executable,
        "started_at_utc": started,
        "finished_at_utc": now(),
        "phase_state": phase_state,
        "resolver_states": resolver_states,
        "declared_capability_profile": {
            "TMHUNT": {
                "scope": "IC025_ONLY",
                "accepted_modes_tested": ["EXACT", "PARTIAL"],
                "exact_zero_semantics_tested": True,
                "excluded_modes_not_tested": ["SPLIT", "WILDCARD"],
                "excluded_modes_coverage_weight": 0
            },
            "TRADEMARKIA": {
                "role": "BROAD_US_FEDERAL_RECORD_RESOLVER",
                "known_positive_search_tested": True,
                "known_record_binding_tested": True,
                "opaque_zero_tested_with_limited_semantics": True,
                "fuzzy_multi_token_behavior_tested": True,
                "query_binding_must_be_stably_attested_before_submit": True
            }
        },
        "required_tm_scope_law": "DECLARED_RESOLVER_CAPABILITY_PROFILE_DOES_NOT_REDUCE_REQUIRED_TM_QUERY_PLAN;_MISSING_REQUIRED_QUERY_DIMENSION_MUST_HOLD",
        "production_tm_decision_authorized": False,
        "external_side_effects_authorized": False,
        "daily7_candidate_queries_executed": False,
        "records": records,
        "repeatability_identity": {
            "commit_sha": os.getenv("GITHUB_SHA", "UNKNOWN"),
            "run_id": os.getenv("GITHUB_RUN_ID", "UNKNOWN"),
            "harness_revision": HARNESS_REVISION,
            "fixed_canaries": ["NIKE", OPAQUE, "JUST DO IT", "AVER QZXJ KESTREL 91372", "50086105"]
        },
        "next_action": "RUN_SECOND_DISTINCT_EXECUTION_ON_SAME_EXACT_COMMIT_AND_SAME_HARNESS" if phase_state == "A4_DECLARED_PROFILE_PASS" else "HOLD_ONLY_FAILED_DECLARED_CAPABILITY;_NO_SPLIT_WILDCARD_RETRY_NO_NEW_BREADTH"
    }
    (OUT / "a4-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({
        "phase_state": phase_state,
        "resolver_states": resolver_states,
        "record_states": [(r["resolver"], r["mode"], r["state"], r.get("failure_signature")) for r in records],
        "excluded_modes_not_tested": ["SPLIT", "WILDCARD"]
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
