#!/usr/bin/env python3
import json
from pathlib import Path

current=json.loads(Path('CURRENT.json').read_text())
engine=json.loads(Path('spec/engine.json').read_text())
live_policy=json.loads(Path('spec/live-readiness.json').read_text())
live_state=json.loads(Path('spec/live-readiness-state.json').read_text())
contract_workflow=Path('.github/workflows/contract-matrix.yml').read_text()

assert current['canonical_repository']=='maichicong835/A-Ver'
assert current['canonical_branch']=='main'
assert current['status']=='PRODUCTION_APPROVED_SCOPED'
assert current['engine_version']=='0.1.0'
assert current['external_side_effects_authorized'] is False
assert current['production_tm_decisions_authorized'] is True
assert engine['mode']=='PRODUCTION_SCOPED'
assert current['authority_files']==['CURRENT.json','spec/engine.json','spec/live-readiness.json','spec/live-readiness-state.json']

for key in [
 'capability_state_may_not_be_serialized_as_tm_decision_state',
 'acceptance_receipt_may_not_release_external_hold',
 'successful_acceptance_layers_remain_closed_unless_materially_invalidated',
 'positive_material_hit_is_not_cancelled_by_another_resolver_negative',
 'query_submission_requires_machine_attested_stable_query_binding',
 'workflow_success_may_not_mask_semantic_acceptance_partial',
 'generic_safe_boolean_output_forbidden','legal_clearance_claim_forbidden',
 'production_approval_does_not_authorize_daily7_live_gate',
 'shadow_integration_may_not_mutate_caller_state',
 'resultset_resolution_success_does_not_imply_tm_pass',
 'broad_positive_resultset_requires_record_binding_and_materiality_review',
 'raw_negative_source_count_may_not_substitute_for_scope_qualified_negative_convergence',
 'workflow_success_does_not_imply_daily7_live_readiness',
 'aver_may_not_self_authorize_daily7_live',
 'any_unproven_live_readiness_gate_blocks_live',
 'no_external_repository_write','no_drive_write','no_marketplace_ledger_write',
 'no_captcha_waf_rate_limit_circumvention'
]: assert current['absolute_invariants'][key] is True, key

s=current['acceptance_snapshot']
for phase in ['A0_TRANSPORT','A1_KNOWN_POSITIVE_BINDING','A2_QUERY_RESULTSET_SEMANTICS','A3_NEGATIVE_RESULTSET_SEMANTICS']:
    assert s[phase]=='PASS_CLOSED'
assert s['A4_DECLARED_CAPABILITY_REPEATABILITY']=='PASS_CLOSED_REPEATABLE_ADB32A9B'
assert s['PRE_PROMOTION_CONTRACT_HARDENING']=='PASS_CLOSED_CONTRACT_MATRIX_34702668801'
assert s['PROMOTION_REVIEW']=='PASS_CLOSED_EXPLICIT_USER_APPROVAL_2026_09_13'
assert s['DAILY7_SHADOW_INTEGRATION']=='PASS_CLOSED_RESULTSET_LAYER_RUN_34722878035'
assert s['SHADOW_DEEP_TM_INTERPRETATION']=='PASS_CLOSED_DEEP_DECISION_CANARY_34749315746'
assert s['tmhunt_split']=='CAPABILITY_EXCLUDED_UNPROVEN_ZERO_COVERAGE_WEIGHT'
assert s['tmhunt_wildcard']=='CAPABILITY_EXCLUDED_UNPROVEN_ZERO_COVERAGE_WEIGHT'

p=current['promotion_closure']
assert p['production_commit_sha']=='689e06afcce007979025e68a095f9646d1d37591'
assert p['daily7_live_gate_authorized'] is False

sh=current['daily7_shadow_closure']
assert sh['workflow_run_id']=='34722878035'
assert sh['artifact_id']=='10306408819'
assert sh['workflow_conclusion']=='success'
assert sh['request_schema_validated'] is True
assert sh['receipt_schema_validated'] is True
assert sh['engine_identity_pin_validated'] is True
assert sh['caller_state_mutation_authorized'] is False
assert sh['drive_mutation_authorized'] is False
assert sh['false_tm_pass_observed'] is False
assert sh['resultset_layer_machine_resolved'] is True
assert len(sh['canaries'])==2
for c in sh['canaries']:
    assert c['tm_decision']=='TM_HOLD'

scope=current['current_reopen_scope']
assert scope['only_layer']=='LIVE_READINESS_G4_SCOPE_COMPLETENESS_AND_DECISION'
assert scope['new_candidate_or_market_discovery_forbidden'] is True
assert scope['only_existing_hold_canaries_authorized'] is True
assert scope['daily7_live_gate_authorized'] is False
assert scope['next_machine_gate']=='G4_SCOPE_SEMANTICS_THEN_OPERATIONAL_PASS_PATH'

assert engine['acceptance']['daily7_shadow_integration']['status']=='PASS_CLOSED_RESULTSET_LAYER_RUN_34722878035'
assert engine['acceptance']['shadow_deep_tm_interpretation']['status']=='PASS_CLOSED_DEEP_DECISION_CANARY_34749315746'
assert engine['acceptance']['shadow_deep_tm_interpretation']['live_gate_authorized'] is False
assert engine['evidence_asymmetry']['tmhunt_ic025_negative_has_zero_class016_negative_convergence_weight'] is True
assert engine['evidence_asymmetry']['scope_qualified_negative_convergence_required_for_pass'] is True
assert engine['scope_completeness_law']['class016_negative_pass_requires_class016_relevant_convergent_evidence'] is True
assert engine['decision_controller']['raw_negative_evidence_distinct_sources_is_observability_only'] is True
assert engine['live_readiness_governor']['aver_may_self_authorize_daily7_live'] is False
assert engine['production_transition']['daily7_live_gate_authorized'] is False
assert engine['external_interface_future']['cross_repo_state_mutation_forbidden'] is True

assert live_policy['authorization_law']['any_unproven_gate_blocks_live'] is True
assert live_policy['authorization_law']['aver_may_emit_daily7_live_authorized'] is False
assert live_state['state_is_evidence_index_not_authorization'] is True
assert live_state['live_authorized'] is False
assert live_state['deep_interpretation_closure']['deep_canary_interpretation_complete'] is True
assert live_state['decision_scope_closure']['existing_canaries_deterministic_for_correct_reason'] is True
assert live_state['decision_scope_closure']['required_query_scope_semantics_complete'] is False

trigger_scope=contract_workflow.split('paths:',1)[1].split('workflow_dispatch:',1)[0]
for forbidden in ['CURRENT.json','spec/engine.json','tests/test_contract.py','docs/']:
    assert forbidden not in trigger_scope

print('AVER_CONTRACT_TEST_PASS')
