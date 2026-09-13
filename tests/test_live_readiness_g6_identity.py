#!/usr/bin/env python3
import copy
import json
from pathlib import Path

from aver.live_readiness import evaluate

current=json.loads(Path('CURRENT.json').read_text())
engine=json.loads(Path('spec/engine.json').read_text())
policy=json.loads(Path('spec/live-readiness.json').read_text())
state=json.loads(Path('spec/live-readiness-state.json').read_text())

# Preserve all already-closed evidence, then inject a canonical-shaped G6 closure.
base=copy.deepcopy(state)
pin=base['daily7_deep_shadow_closure']['aver_pin_sha']
closure={
    'state':'PASS_CLOSED',
    'workflow_repository':'maichicong835/Amazon-Daily7Source',
    'workflow_run_id':'34759089496',
    'daily7_head_sha':'3bf8f833e4616eea9e65152bafb438b95df0e21e',
    'daily7_repo_guard_run_id':'34759089575',
    'daily7_repo_guard_conclusion':'success',
    'aver_pin_sha':pin,
    'artifact_id':'10318167414',
    'artifact_digest':'sha256:8d8bdf9cb971046851d27b7f011cf1fbf5ca108df23c5052d49f517c22064385',
    'same_intended_live_router':'scripts/aver_live_boundary.py',
    'mutation_enabled':False,
    'pass_kill_hold_handling_proven':True,
    'fail_closed_boundary_proven':True,
    'live_without_explicit_authorization_blocked':True,
    'g7_authorized':False,
}
base['live_boundary_rehearsal_closure']=closure

# Governance head intentionally differs from execution pin. That must not block G6.
r=evaluate(current,engine,policy,base,candidate_sha='1'*40,authority_contract_pass=True,contract_matrix_pass=True)
g6=next(g for g in r['gates'] if g['gate_id']=='G6_LIVE_BOUNDARY_REHEARSAL')
assert g6['state']=='PASS'
assert g6['evidence']['expected_execution_pin_from_g5']==pin
assert g6['evidence']['execution_pin_is_governance_head'] is False
assert r['terminal_state']=='READY_FOR_EXPLICIT_LIVE_AUTHORIZATION'
assert r['live_authorized'] is False

# Wrong execution pin must fail closed.
bad=copy.deepcopy(base)
bad['live_boundary_rehearsal_closure']['aver_pin_sha']='2'*40
r=evaluate(current,engine,policy,bad,candidate_sha='1'*40,authority_contract_pass=True,contract_matrix_pass=True)
g6=next(g for g in r['gates'] if g['gate_id']=='G6_LIVE_BOUNDARY_REHEARSAL')
assert g6['state']=='BLOCKED'
assert r['terminal_state']=='BLOCKED'

# Repo Guard failure, mutation, missing fail-closed evidence, or premature G7 all block.
for field,value in [
    ('daily7_repo_guard_conclusion','failure'),
    ('mutation_enabled',True),
    ('fail_closed_boundary_proven',False),
    ('live_without_explicit_authorization_blocked',False),
    ('g7_authorized',True),
]:
    bad=copy.deepcopy(base)
    bad['live_boundary_rehearsal_closure'][field]=value
    r=evaluate(current,engine,policy,bad,candidate_sha='1'*40,authority_contract_pass=True,contract_matrix_pass=True)
    g6=next(g for g in r['gates'] if g['gate_id']=='G6_LIVE_BOUNDARY_REHEARSAL')
    assert g6['state']=='BLOCKED', field

print('AVER_G6_EXECUTION_PIN_IDENTITY_REGRESSION_PASS')
