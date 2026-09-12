#!/usr/bin/env python3
import json
from pathlib import Path

current=json.loads(Path('CURRENT.json').read_text())
engine=json.loads(Path('spec/engine.json').read_text())
contract_workflow=Path('.github/workflows/contract-matrix.yml').read_text()

assert current['canonical_repository']=='maichicong835/A-Ver'
assert current['canonical_branch']=='main'
assert current['status']=='PRODUCTION_APPROVED_SCOPED'
assert current['engine_version']=='0.1.0'
assert current['external_side_effects_authorized'] is False
assert current['production_tm_decisions_authorized'] is True
assert engine['mode']=='PRODUCTION_SCOPED'

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
assert s['SHADOW_DEEP_TM_INTERPRETATION']=='PENDING'
assert s['tmhunt_split']=='CAPABILITY_EXCLUDED_UNPROVEN_ZERO_COVERAGE_WEIGHT'
assert s['tmhunt_wildcard']=='CAPABILITY_EXCLUDED_UNPROVEN_ZERO_COVERAGE_WEIGHT'

p=current['promotion_closure']
assert p['production_commit_sha']=='689e06afcce007979025e68a095f9646d1d37591'
assert p['authority_guard_run_id']=='34722809905'
assert p['authority_guard_conclusion']=='success'
assert p['daily7_live_gate_authorized'] is False

sh=current['daily7_shadow_closure']
assert sh['workflow_run_id']=='34722878035'
assert sh['daily7_head_sha']=='bce20fb9db9e6ff4ff8bfbc1aa67daacbd4e1723'
assert sh['aver_pin_sha']=='689e06afcce007979025e68a095f9646d1d37591'
assert sh['artifact_id']=='10306408819'
assert sh['artifact_digest']=='sha256:7251ad40baf0fad95f348419cd84d24b2cc1fd23d176e1c4d2690ccf640aa036'
assert sh['workflow_conclusion']=='success'
assert sh['machine_marker']=='AVER_DAILY7_SHADOW_PASS'
assert sh['request_schema_validated'] is True
assert sh['receipt_schema_validated'] is True
assert sh['engine_identity_pin_validated'] is True
assert sh['caller_state_mutation_authorized'] is False
assert sh['drive_mutation_authorized'] is False
assert sh['false_tm_pass_observed'] is False
assert sh['resultset_layer_machine_resolved'] is True
assert len(sh['canaries'])==2
for c in sh['canaries']:
    assert c['trademarkia_terminal']=='POSITIVE_RESULTSET'
    assert c['tmhunt_ic025_terminal']=='ZERO_RESULTSET'
    assert c['tm_decision']=='TM_HOLD'
assert sh['remaining_unresolved_layer']=='MATERIAL_RECORD_BINDING_SIMILARITY_G0_G4_AND_REQUIRED_QUERY_SCOPE'

scope=current['current_reopen_scope']
assert scope['only_layer']=='SHADOW_DEEP_TM_INTERPRETATION'
assert scope['new_candidate_or_market_discovery_forbidden'] is True
assert scope['only_existing_hold_canaries_authorized'] is True
assert scope['daily7_live_gate_authorized'] is False
assert scope['next_machine_gate']=='MATERIAL_RECORD_BINDING_SIMILARITY_G0_G4_AND_REQUIRED_QUERY_SCOPE'

assert engine['acceptance']['daily7_shadow_integration']['status']=='PASS_CLOSED_RESULTSET_LAYER_RUN_34722878035'
assert engine['acceptance']['daily7_shadow_integration']['machine_evidence']['workflow_run_id']=='34722878035'
assert engine['acceptance']['daily7_shadow_integration']['machine_evidence']['both_trademarkia_resultsets_resolved'] is True
assert engine['acceptance']['daily7_shadow_integration']['machine_evidence']['both_tm_decisions_hold'] is True
assert engine['acceptance']['shadow_deep_tm_interpretation']['status']=='PENDING'
assert engine['acceptance']['shadow_deep_tm_interpretation']['live_gate_authorized'] is False
assert engine['evidence_asymmetry']['resultset_resolution_success_does_not_imply_tm_pass'] is True
assert engine['evidence_asymmetry']['tmhunt_ic025_negative_has_zero_class016_negative_convergence_weight'] is True
assert engine['scope_completeness_law']['class016_negative_pass_requires_class016_relevant_convergent_evidence'] is True
assert engine['production_transition']['daily7_resultset_shadow_passed'] is True
assert engine['production_transition']['daily7_deep_shadow_pending'] is True
assert engine['production_transition']['daily7_live_gate_authorized'] is False
assert engine['external_interface_future']['cross_repo_state_mutation_forbidden'] is True
assert engine['external_interface_future']['resultset_only_shadow_pass_does_not_authorize_live_gate'] is True

trigger_scope=contract_workflow.split('paths:',1)[1].split('workflow_dispatch:',1)[0]
for forbidden in ['CURRENT.json','spec/engine.json','tests/test_contract.py','docs/']:
    assert forbidden not in trigger_scope

print('AVER_CONTRACT_TEST_PASS')
