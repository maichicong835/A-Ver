#!/usr/bin/env python3
import json
from pathlib import Path

c=json.loads(Path('CURRENT.json').read_text())
e=json.loads(Path('spec/engine.json').read_text())
s=json.loads(Path('spec/live-readiness-state.json').read_text())

assert c['canonical_repository']=='maichicong835/A-Ver'
assert c['canonical_branch']=='main'
assert c['daily7_live_gate_authorized'] is False
assert c['acceptance_snapshot']['G6_LIVE_BOUNDARY_REHEARSAL']=='PASS_CLOSED_DAILY7_G6_REHEARSAL_34759089496'
assert c['current_reopen_scope']['only_layer']=='G7_EXPLICIT_LIVE_AUTHORIZATION'
assert e['acceptance']['live_boundary_rehearsal_g6']['status']=='PASS_CLOSED_DAILY7_G6_REHEARSAL_34759089496'
assert e['production_transition']['g6_live_boundary_rehearsal_passed'] is True
assert e['production_transition']['daily7_live_gate_authorized'] is False
assert s['live_authorized'] is False
g5=s['daily7_deep_shadow_closure']
g6=s['live_boundary_rehearsal_closure']
assert g6['state']=='PASS_CLOSED'
assert g6['aver_pin_sha']==g5['aver_pin_sha']
assert g6['daily7_repo_guard_conclusion']=='success'
assert g6['mutation_enabled'] is False
assert g6['pass_kill_hold_handling_proven'] is True
assert g6['fail_closed_boundary_proven'] is True
assert g6['live_without_explicit_authorization_blocked'] is True
assert g6['g7_authorized'] is False
assert s['g7_explicit_live_authorization']['state']=='AWAITING_EXPLICIT_USER_AUTHORIZATION_AFTER_G1_G6_READY'
print('AVER_CONTRACT_TEST_PASS')
