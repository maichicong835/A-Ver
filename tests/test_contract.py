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
assert snapshot["A4_REPEATABILITY"] == "PARTIAL_OPEN_ONLY_FOR_TMHUNT_POSITIVE_MODE_RESULT_BINDING"
assert snapshot["trademarkia_a4_behavior_matrix"] == "PASS_CLOSED"
assert snapshot["tmhunt_a4_exact_zero_semantics"] == "PASS_CLOSED"

scope = current["current_reopen_scope"]
assert scope["only_layer"] == "A4_TMHUNT_POSITIVE_MODE_RESULT_BINDING"
assert scope["fixed_canaries_only"] is True
assert scope["candidate_or_market_queries_forbidden"] is True
assert scope["new_resolver_discovery_forbidden"] is True
assert scope["a0_a3_rerun_forbidden_without_material_surface_or_harness_invalidation"] is True

closure = current["a4_closure_contract"]
assert closure["active_mode_must_be_machine_attested_not_merely_clicked"] is True
assert closure["submission_must_be_scoped_to_the_active_search_panel"] is True
assert closure["bounded_terminal_dom_state_required"] is True
assert closure["positive_resultset_may_be_proven_by_structured_bound_rows_without_requiring_a_specific_count_string"] is True

repeatability = current["repeatability_contract"]
assert repeatability["second_run_must_be_distinct_github_workflow_run"] is True
assert repeatability["second_run_must_use_same_exact_commit"] is True
assert repeatability["second_run_should_use_workflow_dispatch_without_code_or_authority_change"] is True
assert repeatability["job_rerun_of_the_same_workflow_run_is_not_sufficient"] is True

capability = set(engine["state_machine"]["capability_states"])
tm_states = set(engine["state_machine"]["tm_decision_states"])
assert capability.isdisjoint(tm_states)
assert engine["state_machine"]["acceptance_mode_may_emit_tm_decision_states"] is False

assert engine["resolver_roles"]["TMHUNT"]["declared_scope"] == "IC025"
assert engine["resolver_roles"]["TMHUNT"]["scope_generalization_forbidden"] is True
assert engine["resolver_roles"]["TMHUNT"]["current_a4_positive_mode_binding"] == "UNPROVEN"
assert engine["resolver_roles"]["TRADEMARKIA"]["opaque_zero_may_not_be_generalized_to_arbitrary_multi_token_exact_clearance"] is True

assert engine["evidence_asymmetry"]["search_engine_index_miss_has_zero_negative_clearance_weight"] is True
assert engine["evidence_asymmetry"]["positive_material_hit_is_not_cancelled_by_another_resolver_negative"] is True

anti_loop = engine["anti_loop"]
assert anti_loop["same_resolver_same_stage_same_failure_signature_max_retries"] == 1
assert anti_loop["more_candidate_queries_may_not_answer_systemic_transport_failure"] is True
assert anti_loop["more_candidate_queries_may_not_answer_mode_binding_failure"] is True
assert anti_loop["successful_prior_layers_remain_closed"] is True
assert anti_loop["authority_or_documentation_change_alone_does_not_reopen_closed_layers"] is True

orchestration = engine["orchestration"]
assert orchestration["closed_phase_auto_rerun_on_current_or_spec_change"] is False
assert orchestration["a4_repeatability_second_run_must_use_workflow_dispatch_on_same_exact_commit"] is True
assert orchestration["repeatability_via_commit_touch_or_trigger_file_forbidden"] is True

assert engine["acceptance"]["a4"]["only_open_component"] == "TMHUNT_POSITIVE_MODE_RESULT_BINDING"
assert engine["acceptance"]["a4"]["repeatability_contract"]["same_exact_commit_required"] is True
assert engine["receipts"]["repository_commit_of_runtime_receipts"] is False

transition = engine["production_transition"]
assert transition["promotion_before_a4_repeatability_forbidden"] is True
assert transition["daily7_or_external_caller_integration_before_promotion_forbidden"] is True
assert transition["acceptance_and_production_use_same_resolver_implementation"] is True
assert transition["parallel_reimplementation_of_proven_resolver_logic_forbidden"] is True
assert transition["versioned_request_schema_required"] is True
assert transition["versioned_receipt_schema_required"] is True
assert transition["generic_safe_boolean_output_forbidden"] is True

future = engine["external_interface_future"]
assert future["caller_should_not_track_mutable_main_for_production"] is True
assert future["cross_repo_state_mutation_forbidden"] is True

print("AVER_CONTRACT_TEST_PASS")
