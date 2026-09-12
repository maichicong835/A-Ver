#!/usr/bin/env python3
import json
from pathlib import Path

current = json.loads(Path("CURRENT.json").read_text(encoding="utf-8"))
engine = json.loads(Path("spec/engine.json").read_text(encoding="utf-8"))
a4_source = Path("src/aver/acceptance_a4.py").read_text(encoding="utf-8")
trademarkia_source = Path("src/aver/resolvers/trademarkia.py").read_text(encoding="utf-8")
contract_workflow = Path(".github/workflows/contract-matrix.yml").read_text(encoding="utf-8")

assert current["canonical_repository"] == "maichicong835/A-Ver"
assert current["canonical_branch"] == "main"
assert current["status"] == "PRODUCTION_APPROVED_SCOPED"
assert current["engine_version"] == "0.1.0"
assert current["external_side_effects_authorized"] is False
assert current["production_tm_decisions_authorized"] is True
assert engine["mode"] == "PRODUCTION_SCOPED"

for key in [
    "capability_state_may_not_be_serialized_as_tm_decision_state",
    "acceptance_receipt_may_not_release_external_hold",
    "successful_acceptance_layers_remain_closed_unless_materially_invalidated",
    "authority_or_documentation_change_alone_does_not_reopen_closed_acceptance_layers",
    "positive_material_hit_is_not_cancelled_by_another_resolver_negative",
    "trademarkia_opaque_zero_does_not_imply_exact_negative_semantics_for_arbitrary_multi_token_queries",
    "query_submission_requires_machine_attested_stable_query_binding",
    "workflow_success_may_not_mask_semantic_acceptance_partial",
    "unproven_optional_resolver_mode_may_be_excluded_but_may_not_be_counted_as_coverage",
    "scope_reduction_of_transport_capability_may_not_reduce_required_tm_query_or_safety_scope",
    "acceptance_and_future_production_must_share_resolver_implementation",
    "generic_safe_boolean_output_forbidden",
    "legal_clearance_claim_forbidden",
    "request_data_may_not_override_engine_authority",
    "production_approval_does_not_authorize_daily7_live_gate",
    "shadow_integration_may_not_mutate_caller_state",
    "no_external_repository_write",
    "no_drive_write",
    "no_marketplace_ledger_write",
    "no_captcha_waf_rate_limit_circumvention"
]:
    assert current["absolute_invariants"][key] is True, key

snapshot = current["acceptance_snapshot"]
for phase in ["A0_TRANSPORT", "A1_KNOWN_POSITIVE_BINDING", "A2_QUERY_RESULTSET_SEMANTICS", "A3_NEGATIVE_RESULTSET_SEMANTICS"]:
    assert snapshot[phase] == "PASS_CLOSED", phase
assert snapshot["A4_DECLARED_CAPABILITY_REPEATABILITY"] == "PASS_CLOSED_REPEATABLE_ADB32A9B"
assert snapshot["PRE_PROMOTION_CONTRACT_HARDENING"] == "PASS_CLOSED_CONTRACT_MATRIX_34702668801"
assert snapshot["PROMOTION_REVIEW"] == "PASS_CLOSED_EXPLICIT_USER_APPROVAL_2026_09_13"
assert snapshot["DAILY7_SHADOW_INTEGRATION"] == "AUTHORIZED_NOT_LIVE"
assert snapshot["tmhunt_split"] == "CAPABILITY_EXCLUDED_UNPROVEN_ZERO_COVERAGE_WEIGHT"
assert snapshot["tmhunt_wildcard"] == "CAPABILITY_EXCLUDED_UNPROVEN_ZERO_COVERAGE_WEIGHT"

closure = current["a4_repeatability_closure"]
assert closure["exact_commit_sha"] == "adb32a9b554a420f9dedc1c6d2916bcaec16d9b6"
assert closure["harness_revision"] == "a4.3-query-binding-stability"
assert closure["run_1"]["workflow_run_id"] == "34702194480"
assert closure["run_2"]["workflow_run_id"] == "34702254867"
assert closure["normalized_semantic_states_match"] is True
assert closure["split_wildcard_retested"] is False

contract_closure = current["prepromotion_contract_closure"]
assert contract_closure["tested_commit_sha"] == "6066da673117b80e10655f3833480d225dec0e0c"
assert contract_closure["workflow_run_id"] == "34702668801"
assert contract_closure["workflow_conclusion"] == "success"
assert contract_closure["machine_marker"] == "AVER_CONTRACT_MATRIX_PASS"
assert contract_closure["resolver_transport_executed"] is False

promotion = current["promotion_closure"]
assert promotion["approved_on"] == "2026-09-13"
assert promotion["approval_source"] == "EXPLICIT_USER_INSTRUCTION"
assert promotion["promoted_from_commit_sha"] == "6719628204414ac5003d1f5be9e9d8fb66c1e9f3"
assert promotion["production_tm_decisions_authorized"] is True
assert promotion["external_side_effects_authorized"] is False
assert promotion["daily7_shadow_integration_authorized"] is True
assert promotion["daily7_live_gate_authorized"] is False
assert promotion["cross_repository_state_mutation_authorized"] is False

profile = current["declared_capability_profile"]
assert profile["profile_id"] == "AVER_TM_PROFILE_0_1_SCOPED"
assert profile["TMHUNT"]["accepted_modes"] == ["EXACT", "PARTIAL"]
assert set(profile["TMHUNT"]["excluded_unproven_modes"]) == {"SPLIT", "WILDCARD"}
assert profile["TMHUNT"]["excluded_modes_have_zero_coverage_weight"] is True
assert profile["TRADEMARKIA"]["query_binding_stability_required_before_submit"] is True

for path in [
    "src/aver/resolvers/__init__.py",
    "src/aver/resolvers/common.py",
    "src/aver/resolvers/tmhunt.py",
    "src/aver/resolvers/trademarkia.py",
    "src/aver/decision.py",
    "spec/request.schema.json",
    "spec/receipt.schema.json",
    "tests/test_contract_matrix.py",
    ".github/workflows/contract-matrix.yml"
]:
    assert Path(path).is_file(), path

assert "from resolvers import TMHuntResolver, TrademarkiaResolver" in a4_source
assert 'HARNESS_REVISION = "a4.3-query-binding-stability"' in a4_source
assert 'tmhunt.query("SPLIT"' not in a4_source
assert 'tmhunt.query("WILDCARD"' not in a4_source
assert "def _bind_query_stably" in trademarkia_source
assert "TRADEMARKIA_QUERY_BINDING_UNSTABLE_BEFORE_SUBMIT" in trademarkia_source

interface = current["interface_contract"]
assert interface["request_schema_version"] == "1.0"
assert interface["receipt_schema_version"] == "1.0"
assert interface["generic_safe_boolean_forbidden"] is True
assert interface["legal_clearance_asserted_must_be_false"] is True
assert interface["negative_pass_min_distinct_evidence_sources"] == 2

scope = current["current_reopen_scope"]
assert scope["only_layer"] == "DAILY7_SHADOW_INTEGRATION"
assert scope["resolver_revalidation_forbidden_without_material_invalidation"] is True
assert scope["new_candidate_or_market_discovery_forbidden"] is True
assert scope["only_existing_hold_canaries_authorized"] is True
assert scope["daily7_shadow_integration_authorized"] is True
assert scope["daily7_live_gate_authorized"] is False
assert scope["production_tm_decisions_authorized"] is True
assert scope["next_machine_gate"] == "SHADOW_RECEIPT_IDENTITY_SCHEMA_DECISION_VALIDATION"

assert engine["acceptance"]["a4"]["status"] == "PASS_CLOSED_REPEATABLE_ADB32A9B"
assert engine["acceptance"]["pre_promotion_contract_hardening"]["status"] == "PASS_CLOSED_CONTRACT_MATRIX_34702668801"
promo = engine["acceptance"]["promotion_review"]
assert promo["status"] == "PASS_CLOSED_EXPLICIT_USER_APPROVAL_2026_09_13"
assert promo["production_state_change_authorized"] is True
assert promo["daily7_shadow_integration_authorized"] is True
assert promo["daily7_live_gate_authorized"] is False
shadow = engine["acceptance"]["daily7_shadow_integration"]
assert shadow["status"] == "AUTHORIZED_NOT_LIVE"
assert shadow["existing_hold_canaries_only"] is True
assert shadow["caller_state_mutation_forbidden"] is True
assert shadow["live_gate_authorized"] is False

assert engine["state_machine"]["production_mode_may_emit_tm_decision_states"] is True
assert engine["interface_contract"]["request_schema_version"] == "1.0"
assert engine["interface_contract"]["receipt_schema_version"] == "1.0"
assert engine["decision_controller"]["negative_evidence_distinct_sources_min_for_pass"] == 2
assert engine["decision_controller"]["tm_pass_is_legal_clearance"] is False
assert engine["orchestration"]["shadow_integration_is_separate_from_live_gate"] is True
assert engine["production_transition"]["promotion_state"] == "PROMOTED_SCOPED"
assert engine["production_transition"]["production_tm_decisions_authorized"] is True
assert engine["production_transition"]["external_side_effects_authorized"] is False
assert engine["production_transition"]["daily7_shadow_integration_authorized"] is True
assert engine["production_transition"]["daily7_live_gate_authorized"] is False
assert engine["external_interface_future"]["cross_repo_state_mutation_forbidden"] is True

trigger_scope = contract_workflow.split("paths:", 1)[1].split("workflow_dispatch:", 1)[0]
assert "CURRENT.json" not in trigger_scope
assert "spec/engine.json" not in trigger_scope
assert "tests/test_contract.py" not in trigger_scope
assert "docs/" not in trigger_scope

print("AVER_CONTRACT_TEST_PASS")
