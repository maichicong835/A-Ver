#!/usr/bin/env python3
import json
from pathlib import Path

current = json.loads(Path("CURRENT.json").read_text(encoding="utf-8"))
engine = json.loads(Path("spec/engine.json").read_text(encoding="utf-8"))
a4_source = Path("src/aver/acceptance_a4.py").read_text(encoding="utf-8")

assert current["canonical_repository"] == "maichicong835/A-Ver"
assert current["canonical_branch"] == "main"
assert current["status"] == "ACCEPTANCE_ONLY"
assert current["engine_version"] == "0.1.0"
assert current["external_side_effects_authorized"] is False
assert current["production_tm_decisions_authorized"] is False

for key in [
    "capability_state_may_not_be_serialized_as_tm_decision_state",
    "acceptance_receipt_may_not_release_external_hold",
    "successful_acceptance_layers_remain_closed_unless_materially_invalidated",
    "authority_or_documentation_change_alone_does_not_reopen_closed_acceptance_layers",
    "positive_material_hit_is_not_cancelled_by_another_resolver_negative",
    "trademarkia_opaque_zero_does_not_imply_exact_negative_semantics_for_arbitrary_multi_token_queries",
    "unproven_optional_resolver_mode_may_be_excluded_but_may_not_be_counted_as_coverage",
    "scope_reduction_of_transport_capability_may_not_reduce_required_tm_query_or_safety_scope",
    "acceptance_and_future_production_must_share_resolver_implementation",
    "no_external_repository_write",
    "no_drive_write",
    "no_marketplace_ledger_write",
    "no_captcha_waf_rate_limit_circumvention"
]:
    assert current["absolute_invariants"][key] is True, key

snapshot = current["acceptance_snapshot"]
for phase in ["A0_TRANSPORT", "A1_KNOWN_POSITIVE_BINDING", "A2_QUERY_RESULTSET_SEMANTICS", "A3_NEGATIVE_RESULTSET_SEMANTICS"]:
    assert snapshot[phase] == "PASS_CLOSED", phase
assert snapshot["A4_DECLARED_CAPABILITY_REPEATABILITY"] == "SCOPED_PROFILE_FROZEN_PENDING_REPEATABILITY_RUN_1"
assert snapshot["tmhunt_exact_positive"] == "PASS_PROVEN_RUN_34700639830"
assert snapshot["tmhunt_partial_positive"] == "PASS_PROVEN_RUN_34700639830"
assert snapshot["tmhunt_split"] == "CAPABILITY_EXCLUDED_UNPROVEN_ZERO_COVERAGE_WEIGHT"
assert snapshot["tmhunt_wildcard"] == "CAPABILITY_EXCLUDED_UNPROVEN_ZERO_COVERAGE_WEIGHT"

profile = current["declared_capability_profile"]
assert profile["profile_id"] == "AVER_TM_PROFILE_0_1_SCOPED"
assert profile["TMHUNT"]["accepted_modes"] == ["EXACT", "PARTIAL"]
assert set(profile["TMHUNT"]["excluded_unproven_modes"]) == {"SPLIT", "WILDCARD"}
assert profile["TMHUNT"]["excluded_modes_have_zero_coverage_weight"] is True
assert profile["TRADEMARKIA"]["multi_token_exact_negative_clearance_from_opaque_zero_forbidden"] is True

shared = current["shared_resolver_lock"]
assert shared["shared_module_root"] == "src/aver/resolvers"
assert shared["scoped_a4_must_import_shared_resolvers"] is True
assert shared["future_production_must_import_same_resolvers"] is True
assert shared["parallel_production_resolver_reimplementation_forbidden"] is True
for path in [
    "src/aver/resolvers/__init__.py",
    "src/aver/resolvers/common.py",
    "src/aver/resolvers/tmhunt.py",
    "src/aver/resolvers/trademarkia.py"
]:
    assert Path(path).is_file(), path
assert "from resolvers import TMHuntResolver, TrademarkiaResolver" in a4_source
assert 'tmhunt.query("SPLIT"' not in a4_source
assert 'tmhunt.query("WILDCARD"' not in a4_source
assert 'tmhunt.query("EXACT"' in a4_source
assert 'tmhunt.query("PARTIAL"' in a4_source

scope = current["current_reopen_scope"]
assert scope["only_layer"] == "A4_SCOPED_PROFILE_REPEATABILITY"
assert scope["retry_tmhunt_split_forbidden"] is True
assert scope["retry_tmhunt_wildcard_forbidden"] is True
assert scope["candidate_or_market_queries_forbidden"] is True
assert scope["new_resolver_discovery_forbidden"] is True

scope_law = current["scope_completeness_law"]
assert scope_law["required_tm_query_plan_must_remain_complete"] is True
assert scope_law["excluded_capability_has_zero_coverage_weight"] is True
assert scope_law["if_authorized_capabilities_cannot_complete_a_required_query_dimension"] == "TM_HOLD_EVIDENCE_NOT_TM_PASS"

repeatability = current["repeatability_contract"]
assert repeatability["declared_profile_is_frozen"] is True
assert repeatability["first_and_second_runs_must_be_distinct_github_workflow_runs"] is True
assert repeatability["both_runs_must_use_same_exact_commit"] is True
assert repeatability["excluded_modes_are_not_retested"] is True
assert repeatability["same_run_job_rerun_is_not_sufficient"] is True
assert repeatability["isolated_repeatability_ref_creation_is_allowed_when_dispatch_tooling_is_unavailable"] is True
assert repeatability["repeatability_ref_must_point_to_same_exact_commit"] is True

capability = set(engine["state_machine"]["capability_states"])
tm_states = set(engine["state_machine"]["tm_decision_states"])
assert capability.isdisjoint(tm_states)
assert "CAPABILITY_EXCLUDED_UNPROVEN" in capability
assert engine["state_machine"]["acceptance_mode_may_emit_tm_decision_states"] is False

tmhunt = engine["resolver_roles"]["TMHUNT"]
assert tmhunt["declared_scope"] == "IC025"
assert tmhunt["accepted_modes"] == ["EXACT", "PARTIAL"]
assert set(tmhunt["excluded_unproven_modes"].keys()) == {"SPLIT", "WILDCARD"}
assert tmhunt["excluded_modes_have_zero_scope_coverage_weight"] is True
assert tmhunt["same_strategy_retry_of_excluded_modes_forbidden"] is True

tria = engine["resolver_roles"]["TRADEMARKIA"]
assert tria["opaque_zero_may_not_be_generalized_to_arbitrary_multi_token_exact_clearance"] is True
assert tria["closed_layer_incidental_recheck_miss_does_not_reopen_without_material_invalidation"] is True

query_plan = engine["query_plan"]
assert query_plan["resolver_mode_and_query_stage_are_not_synonyms"] is True
assert query_plan["negative_pass_requires_required_query_scope_complete"] is True
assert query_plan["missing_required_query_dimension"] == "TM_HOLD_EVIDENCE_NOT_TM_PASS"

anti_loop = engine["anti_loop"]
assert anti_loop["same_resolver_same_stage_same_failure_signature_max_retries"] == 1
assert anti_loop["after_causal_repair_unproven_optional_mode"].startswith("EXCLUDE_CAPABILITY")
assert anti_loop["more_candidate_queries_may_not_answer_mode_binding_failure"] is True
assert anti_loop["successful_prior_layers_remain_closed"] is True

orchestration = engine["orchestration"]
assert orchestration["closed_phase_auto_rerun_on_current_or_spec_change"] is False
assert orchestration["phase_auto_run_allowed_when_its_own_harness_or_shared_resolver_changes"] is True
assert orchestration["repeatability_ref_must_point_to_same_exact_commit"] is True
assert orchestration["authority_guard_is_separate_from_resolver_acceptance"] is True

assert engine["shared_resolver_implementation"]["module_root"] == "src/aver/resolvers"
assert engine["shared_resolver_implementation"]["parallel_resolver_implementation_forbidden"] is True

a4 = engine["acceptance"]["a4"]
assert a4["status"] == "SCOPED_PROFILE_FROZEN_PENDING_REPEATABILITY_RUN_1"
assert a4["tmhunt_modes_under_test"] == ["EXACT", "PARTIAL"]
assert set(a4["tmhunt_excluded_modes_not_tested"]) == {"SPLIT", "WILDCARD"}
assert a4["repeatability_contract"]["same_exact_commit_required"] is True
assert a4["repeatability_contract"]["excluded_modes_must_not_be_retested"] is True

assert engine["scope_completeness_law"]["required_tm_query_plan_must_still_be_complete"] is True
assert engine["scope_completeness_law"]["if_authorized_resolvers_cannot_complete_required_query_plan"] == "TM_HOLD_EVIDENCE"
assert engine["receipts"]["repository_commit_of_runtime_receipts"] is False

transition = engine["production_transition"]
assert transition["promotion_before_declared_profile_repeatability_forbidden"] is True
assert transition["daily7_or_external_caller_integration_before_promotion_forbidden"] is True
assert transition["acceptance_and_production_use_same_resolver_implementation"] is True
assert transition["versioned_request_schema_required"] is True
assert transition["versioned_receipt_schema_required"] is True
assert transition["full_contract_state_coverage_test_required"] is True
assert transition["generic_safe_boolean_output_forbidden"] is True

future = engine["external_interface_future"]
assert future["caller_should_not_track_mutable_main_for_production"] is True
assert future["cross_repo_state_mutation_forbidden"] is True
assert future["daily7_shadow_integration_required_before_live_tm_gate"] is True

print("AVER_CONTRACT_TEST_PASS")
