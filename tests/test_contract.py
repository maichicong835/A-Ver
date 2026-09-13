#!/usr/bin/env python3
import json
from pathlib import Path

current=json.loads(Path('CURRENT.json').read_text())
engine=json.loads(Path('spec/engine.json').read_text())
state=json.loads(Path('spec/live-readiness-state.json').read_text())
contract_workflow=Path('.github/workflows/contract-matrix.yml').read_text()

assert current['canonical_repository']=='maichicong835/A-Ver'
assert current['canonical_branch']=='main'
assert current['status']=='PRODUCTION_APPROVED_SCOPED'
assert current['engine_version']=='0.1.0'
assert current['external_side_effects_authorized'] is False
assert current['daily7_live_gate_authorized'] is False
assert engine['mode']=='PRODUCTION_SCOPED'
assert current['authority_files']==['CURRENT.json','spec/engine.json','spec/live-readiness.json','spec/live-readiness-state.json']

snapshot=current['acceptance_snapshot']
for phase in ['A0_TRANSPORT','A1_KNOWN_POSITIVE_BINDING','A2_QUERY_RESULTSET_SEMANTICS','A3_NEGATIVE_RESULTSET_SEMANTICS']:
    assert snapshot[phase]=='PASS_CLOSED'
assert snapshot['A4_DECLARED_CAPABILITY_REPEATABILITY']=='PASS_CLOSED_REPEATABLE_ADB32A9B'
assert snapshot['DAILY7_SHADOW_INTEGRATION']=='PASS_CLOSED_RESULTSET_LAYER_RUN_34722878035'
assert snapshot['SHADOW_DEEP_TM_INTERPRETATION']=='PASS_CLOSED_DEEP_DECISION_CANARY_34749315746'
assert snapshot['LIVE_READINESS_G4_SCOPE_COMPLETENESS_AND_DECISION']=='PASS_CLOSED_G4B_PRODUCTION_SHAPED_TM_PASS_34752804112'
assert snapshot['G5_DAILY7_DEEP_SHADOW']=='PASS_CLOSED_DAILY7_DEEP_SHADOW_34756443557'
assert snapshot['G6_LIVE_BOUNDARY_REHEARSAL']=='PASS_CLOSED_DAILY7_LIVE_BOUNDARY_34759089496'

scope=current['current_reopen_scope']
assert scope['only_layer']=='G7_EXPLICIT_LIVE_AUTHORIZATION'
assert scope['next_machine_gate']=='G7_REVIEW_READY_RECEIPT_THEN_EXPLICIT_USER_AUTHORIZATION'
assert scope['daily7_live_gate_authorized'] is False
assert current['live_readiness_governance']['current_machine_first_blocking_gate'] is None
assert current['live_readiness_governance']['expected_terminal_after_g6_closure']=='READY_FOR_EXPLICIT_LIVE_AUTHORIZATION'

assert engine['acceptance']['live_readiness_g4']['status']=='PASS_CLOSED_G4B_PRODUCTION_SHAPED_TM_PASS_34752804112'
assert engine['acceptance']['daily7_deep_shadow_g5']['status']=='PASS_CLOSED_DAILY7_DEEP_SHADOW_34756443557'
assert engine['acceptance']['live_boundary_rehearsal_g6']['status']=='PASS_CLOSED_DAILY7_LIVE_BOUNDARY_34759089496'
assert engine['acceptance']['live_boundary_rehearsal_g6']['live_gate_authorized'] is False
assert engine['production_transition']['g6_live_boundary_rehearsal_pending'] is False
assert engine['production_transition']['g6_live_boundary_rehearsal_passed'] is True
assert engine['production_transition']['daily7_live_gate_authorized'] is False
assert engine['decision_controller']['scope_qualified_negative_evidence_distinct_sources_min_for_pass']==2
assert engine['live_readiness_governor']['closed_gate_execution_pin_may_differ_from_governance_head_only_when_semantic_manifest_matches'] is True
assert engine['live_readiness_governor']['g6_rehearsal_must_bind_g5_execution_pin'] is True
assert engine['live_readiness_governor']['ready_state_still_requires_separate_g7_user_authorization'] is True

assert state['state_is_evidence_index_not_authorization'] is True
assert state['live_authorized'] is False
decision_scope=state['decision_scope_closure']
assert decision_scope['required_query_scope_semantics_complete'] is True
assert decision_scope['class016_clean_pass_path_machine_proven'] is True
g5=state['daily7_deep_shadow_closure']
assert g5['state']=='PASS_CLOSED'
assert g5['workflow_run_id']=='34756443557'
assert g5['aver_pin_sha']=='fba76d8e90d9a6e3c01721228362ba70529d94c6'
assert g5['artifact_id']=='10317692195'
assert g5['artifact_digest']=='sha256:730be8d14f89396be2aad22dbe5f363abebcce858d41723c545b9e0ebf26c24b'
assert g5['request_schema_validated'] is True
assert g5['receipt_schema_validated'] is True
assert g5['caller_mutation_observed'] is False
assert g5['drive_mutation_observed'] is False
assert g5['used_reserve_mutation_observed'] is False
assert g5['false_tm_pass_observed'] is False
assert g5['false_tm_kill_observed'] is False
assert g5['semantic_pin_manifest_must_match_current_governance_head'] is True
assert set(g5['semantic_pin_manifest'])=={'src/aver/deep_decision_canary.py','src/aver/decision.py','src/aver/similarity.py','spec/request.schema.json','spec/receipt.schema.json'}

g6=state['live_boundary_rehearsal_closure']
assert g6['state']=='PASS_CLOSED'
assert g6['workflow_run_id']=='34759089496'
assert g6['daily7_head_sha']=='3bf8f833e4616eea9e65152bafb438b95df0e21e'
assert g6['daily7_repo_guard_run_id']=='34759089575'
assert g6['daily7_repo_guard_conclusion']=='success'
assert g6['aver_pin_sha']==g5['aver_pin_sha']=='fba76d8e90d9a6e3c01721228362ba70529d94c6'
assert g6['artifact_id']=='10318167414'
assert g6['artifact_digest']=='sha256:8d8bdf9cb971046851d27b7f011cf1fbf5ca108df23c5052d49f517c22064385'
assert g6['same_intended_live_router']=='scripts/aver_live_boundary.py'
assert g6['mutation_enabled'] is False
assert g6['pass_kill_hold_handling_proven'] is True
assert g6['fail_closed_boundary_proven'] is True
assert g6['live_without_explicit_authorization_blocked'] is True
assert g6['g7_authorized'] is False
assert state['g7_explicit_live_authorization']['state']=='AWAITING_EXPLICIT_USER_AUTHORIZATION_AFTER_G1_G6_READY'

trigger_scope=contract_workflow.split('paths:',1)[1].split('workflow_dispatch:',1)[0]
for forbidden in ['CURRENT.json','spec/engine.json','tests/test_contract.py','docs/']:
    assert forbidden not in trigger_scope

print('AVER_CONTRACT_TEST_PASS')
