#!/usr/bin/env python3
import json
from pathlib import Path

current = json.loads(Path("CURRENT.json").read_text(encoding="utf-8"))
engine = json.loads(Path("spec/engine.json").read_text(encoding="utf-8"))

assert current["canonical_repository"] == "maichicong835/A-Ver"
assert current["canonical_branch"] == "main"
assert current["status"] == "ACCEPTANCE_ONLY"
assert current["external_side_effects_authorized"] is False
assert current["production_tm_decisions_authorized"] is False

inv = current["absolute_invariants"]
for key in [
    "capability_state_may_not_be_serialized_as_tm_decision_state",
    "acceptance_receipt_may_not_release_external_hold",
    "no_external_repository_write",
    "no_drive_write",
    "no_marketplace_ledger_write",
    "no_captcha_waf_rate_limit_circumvention"
]:
    assert inv[key] is True, key

capability = set(engine["state_machine"]["capability_states"])
tm_states = set(engine["state_machine"]["tm_decision_states"])
assert capability.isdisjoint(tm_states)
assert engine["state_machine"]["acceptance_mode_may_emit_tm_decision_states"] is False
assert engine["resolver_roles"]["TMHUNT"]["declared_scope"] == "IC025"
assert engine["resolver_roles"]["TMHUNT"]["scope_generalization_forbidden"] is True
assert engine["evidence_asymmetry"]["search_engine_index_miss_has_zero_negative_clearance_weight"] is True
assert engine["anti_loop"]["more_candidate_queries_may_not_answer_systemic_transport_failure"] is True
assert engine["receipts"]["repository_commit_of_runtime_receipts"] is False

print("AVER_CONTRACT_TEST_PASS")
