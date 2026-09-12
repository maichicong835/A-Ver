#!/usr/bin/env python3
import json
from pathlib import Path

current = json.loads(Path("CURRENT.json").read_text(encoding="utf-8"))
engine = json.loads(Path("spec/engine.json").read_text(encoding="utf-8"))

assert current["canonical_repository"] == "maichicong835/A-Ver"
assert current["canonical_branch"] == "main"
assert current["status"] == "ACCEPTANCE_ONLY"
assert current["engine_version"] == "0.1.0"
assert current["external_side_effects_authorized"] is False
assert current["production_tm_decisions_authorized"] is False

inv = current["absolute_invariants"]
for key in [
    "capability_state_may_not_be_serialized_as_tm_decision_state",
    "acceptance_receipt_may_not_release_external_hold",
    "successful_acceptance_layers_remain_closed_unless_materially_invalidated",
    "authority_or_documentation_change_alone_does_not_reopen_closed_acceptance_layers",
    "positive_material_hit_is_not_cancelled_by_another_resolver_negative",
    "trademarkia_opaque_zero_does_not_imply_exact_negative_semantics_for_arbitrary_multi_token_queries",
    "no_new_resolver_or_candidate_breadth_to_repair_a4_mode_binding",
    "unproven_optional_resolver_mode_may_be_excluded_but_may_not_be_counted_as_coverage",
    "scope_reduction_of_transport_capability_may_not_reduce_required_tm_query_or_safety_scope",
    "production_promotion_may_not_reimplement_resolver_logic_separately_from_proven_acceptance_primitives",
    "no_external_repository_write",
    "no_drive_write",
    "no_marketplace_ledger_write",
    "no_captcha_waf_rate_limit_circumvention",
]:
    assert inv[key] is True, key

snapshot = current["acceptance_snapshot"]
for phase in ["A0_TRANSPORT", "A1_KNOWN_POSITIVE_BINDING", "A2_QUERY_RESULTSET_SEMANTICS", "A3_NEGATIVE_RESULTSET_SEMANTICS"]:
    assert snapshot[phase] == "PASS_CLOSED", phase
assert snapshot["A4_DECLARED_CAPABILITY_REPEATABILITY"] == "PARTIAL_SCOPE_FREEZE_REQUIRED_AFTER_CAUSAL_REPAIR"
assert snapshot["trademarkia_behavior_capability"] == "PASS_CLOSED_FROM_PRIOR_MACHINE_PROVEN_RUNS"
assert snapshot["tmhunt_exact_zero_semantics"] == "PASS_CLOSED"
assert snapshot["tmhunt_exact_positive"] == "PASS_PROVEN_RUN_34700639830"
assert snapshot["tmhunt_partial_positive"] == "PASS_PROVEN_RUN_34700639830"
assert snapshot["tmhunt_split"].startswith("HOLD_CAPABILITY_")
assert snapshot["tmhunt_wildcard"].startswith("HOLD_CAPABILITY_")

evidence = current["latest_causal_repair_evidence"]
assert evidence["commit_sha"] == "2ccc13cfad2db042fcc7ffda49c640a69f3187a6"
assert evidence["workflow_run_id"] == "34700639830"
assert evidence["workflow_job_id"] == "103571660230"
assert evidence["artifact_id"] == "10299693567"
assert evidence["tmhunt_exact_positive"] == "MODE_PASS"
assert evidence["tmhunt_partial_positive"] == "MODE_PASS"
assert evidence["tmhunt_split"] == "TMHUNT_PANEL_SEARCH_INPUT_NOT_FOUND"
assert evidence["tmhunt_wildcard"] == "TMHUNT_PANEL_SEARCH_INPUT_NOT_FOUND"
assert evidence["candidate_queries_executed"] is False
assert evidence["production_decisions_authorized"] is False

profile = current["declared_capability_profile_candidate"]
assert profile["TMHUNT"]["accepted_modes"] == ["EXACT", "PARTIAL"]
assert set(profile["TMHUNT"]["excluded_unproven_modes"]) == {"SPLIT", "WILDCARD"}
assert profile["TMHUNT"]["excluded_modes_have_zero_coverage_weight"] is True
assert profile["TRADEMARKIA"]["multi_token_exact_negative_clearance_from_opaque_zero_forbidden"] is True

scope = current["current_reopen_scope"]
assert scope["only_layer"] == "A4_DECLARED_CAPABILITY_PROFILE_FREEZE_AND_REPEATABILITY"
assert scope["retry_tmhunt_split_forbidden"] is True
assert scope["retry_tmhunt_wildcard_forbidden"] is True
assert scope["candidate_or_market_queries_forbidden"] is True
assert scope["new_resolver_discovery_forbidden"] is True
assert scope["closed_component_recheck_noise_may_not_downgrade_prior_proven_capability_without_material_invalidation"] is True

closure = current["a4_scoped_closure_contract"]
assert closure["full_site_ui_mode_matrix_is_not_a_production_requirement_when_unproven_modes_are_explicitly_excluded"] is True
assert closure["declared_profile_may_include_only_machine_proven_capabilities"] is True
assert closure["unavailable_mode_may_not_be_silently_substituted_or_counted_as_coverage"] is True
assert closure["required_tm_query_plan_must_still_be_complete_using_authorized_capabilities"] is True
assert closure["if_required_query_dimension_cannot_be_completed_with_authorized_capabilities"] == "TM_HOLD_EVIDENCE_NOT_TM_PASS"
assert closure["no_same_strategy_retry_for_split_or_wildcard"] is True

repeatability = current["repeatability_contract"]
assert repeatability["requires_declared_capability_profile_freeze_first"] is True
assert repeatability["second_run_must_be_distinct_github_workflow_run"] is True
assert repeatability["repeatability_runs_must_use_same_exact_commit"] is True
assert repeatability["excluded_modes_are_not_retested_for_repeatability"] is True
assert repeatability["job_rerun_of_the_same_workflow_run_is_not_sufficient"] is True

capability = set(engine["state_machine"]["capability_states"])
tm_states = set(engine["state_machine"]["tm_decision_states"])
assert capability.isdisjoint(tm_states)
assert "CAPABILITY_EXCLUDED_UNPROVEN" in capability
assert engine["state_machine"]["acceptance_mode_may_emit_tm_decision_states"] is False

tmhunt = engine["resolver_roles"]["TMHUNT"]
assert tmhunt["declared_scope"] == "IC025"
assert tmhunt["scope_generalization_forbidden"] is True
assert tmhunt["accepted_modes_candidate"] == ["EXACT", "PARTIAL"]
assert set(tmhunt["excluded_unproven_modes"].keys()) == {"SPLIT", "WILDCARD"}
assert tmhunt["excluded_modes_have_zero_scope_coverage_weight"] is True
assert tmhunt["same_strategy_retry_of_excluded_modes_forbidden"] is True

tria = engine["resolver_roles"]["TRADEMARKIA"]
assert tria["opaque_zero_may_not_be_generalized_to_arbitrary_multi_token_exact_clearance"] is True
assert tria["closed_layer_incidental_recheck_miss_does_not_reopen_without_material_invalidation"] is True

query_plan = engine["query_plan"]
assert query_plan["resolver_mode_and_query_stage_are_not_synonyms"] is True
assert query_plan["tmhunt_split_or_wildcard_is_not_required_if_required_query_stage_is_completed_by_an_authorized_resolver"] is True
assert query_plan["negative_pass_requires_required_query_scope_complete"] is True
assert query_plan["missing_required_query_dimension"] == "TM_HOLD_EVIDENCE_NOT_TM_PASS"

anti_loop = engine["anti_loop"]
assert anti_loop["same_resolver_same_stage_same_failure_signature_max_retries"] == 1
assert anti_loop["after_causal_repair_unproven_optional_mode"].startswith("EXCLUDE_CAPABILITY")
assert anti_loop["more_candidate_queries_may_not_answer_mode_binding_failure"] is True
assert anti_loop["successful_prior_layers_remain_closed"] is True
assert anti_loop["closed_layer_incidental_recheck_noise_does_not_override_prior_proven_state_without_material_invalidation"] is True

orchestration = engine["orchestration"]
assert orchestration["closed_phase_auto_rerun_on_current_or_spec_change"] is False
assert orchestration["repeatability_second_run_must_use_workflow_dispatch_on_same_exact_commit"] is True
assert orchestration["repeatability_via_commit_touch_or_trigger_file_forbidden"] is True
assert orchestration["authority_guard_is_separate_from_resolver_acceptance"] is True

a4 = engine["acceptance"]["a4"]
assert a4["next_component"] == "DECLARED_CAPABILITY_PROFILE_REPEATABILITY"
assert set(a4["excluded_components"]) == {"TMHUNT_SPLIT", "TMHUNT_WILDCARD"}
assert a4["excluded_components_may_not_be_retried_or_counted_as_coverage"] is True

scope_law = engine["scope_completeness_law"]
assert scope_law["full_site_ui_feature_coverage_is_not_equal_to_tm_safety_scope"] is True
assert scope_law["required_tm_query_plan_must_still_be_complete"] is True
assert scope_law["if_authorized_resolvers_cannot_complete_required_query_plan"] == "TM_HOLD_EVIDENCE"

assert engine["receipts"]["repository_commit_of_runtime_receipts"] is False

transition = engine["production_transition"]
assert transition["promotion_before_declared_profile_repeatability_forbidden"] is True
assert transition["daily7_or_external_caller_integration_before_promotion_forbidden"] is True
assert transition["acceptance_and_production_use_same_resolver_implementation"] is True
assert transition["parallel_reimplementation_of_proven_resolver_logic_forbidden"] is True
assert transition["versioned_request_schema_required"] is True
assert transition["versioned_receipt_schema_required"] is True
assert transition["full_contract_state_coverage_test_required"] is True
assert transition["generic_safe_boolean_output_forbidden"] is True

future = engine["external_interface_future"]
assert future["caller_should_not_track_mutable_main_for_production"] is True
assert future["cross_repo_state_mutation_forbidden"] is True
assert future["daily7_shadow_integration_required_before_live_tm_gate"] is True

print("AVER_CONTRACT_TEST_PASS")
