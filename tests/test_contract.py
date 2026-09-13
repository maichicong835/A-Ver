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
assert snapshot['LIVE_READINESS_G4_SCOPE_COMPLETENESS_AND_DECISION']=='PENDING'

scope=current['current_reopen_scope']
assert scope['only_layer']=='LIVE_READINESS_G4_SCOPE_COMPLETENESS_AND_DECISION'
assert scope['next_machine_gate']=='G4_SCOPE_SEMANTICS_THEN_OPERATIONAL_PASS_PATH'
assert scope['daily7_live_gate_authorized'] is False

assert current['deep_interpretation_closure']['workflow_run_id']=='34749315746'
assert current['deep_interpretation_closure']['false_tm_pass_observed'] is False
assert current['deep_interpretation_closure']['false_tm_kill_observed'] is False
assert current['deep_interpretation_closure']['required_query_scope_complete'] is False

assert engine['acceptance']['shadow_deep_tm_interpretation']['status']=='PASS_CLOSED_DEEP_DECISION_CANARY_34749315746'
assert engine['acceptance']['live_readiness_g4']['status']=='PENDING'
assert engine['decision_controller']['scope_qualified_negative_evidence_distinct_sources_min_for_pass']==2
assert engine['live_readiness_governor']['any_unproven_gate_blocks_live'] is True
assert engine['live_readiness_governor']['aver_may_self_authorize_daily7_live'] is False

assert state['state_is_evidence_index_not_authorization'] is True
assert state['live_authorized'] is False
assert state['deep_interpretation_closure']['deep_canary_interpretation_complete'] is True
assert state['decision_scope_closure']['existing_canaries_deterministic_for_correct_reason'] is True
assert state['decision_scope_closure']['required_query_scope_semantics_complete'] is False

trigger_scope=contract_workflow.split('paths:',1)[1].split('workflow_dispatch:',1)[0]
for forbidden in ['CURRENT.json','spec/engine.json','tests/test_contract.py','docs/']:
    assert forbidden not in trigger_scope

print('AVER_CONTRACT_TEST_PASS')
