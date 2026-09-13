#!/usr/bin/env python3
import json
from pathlib import Path

c=json.loads(Path('CURRENT.json').read_text())
e=json.loads(Path('spec/engine.json').read_text())
s=json.loads(Path('spec/live-readiness-state.json').read_text())

PIN='ace5e9b73175ad40ee536606bf2923c8d4ead6a2'
DAILY7_HEAD='e8cf6c8981564c26f35a06e7851ccb7c6db16af4'
DAILY7_GUARD_RUN='34788711663'
DAILY7_PROOF_RUN='34788711694'
ARTIFACT='10327650300'
DIGEST='sha256:9a21ec3cfcaff2e5cb538abfdc09accf6f4dfd22137b29e8a52f7b04ebbfb706'

assert c['canonical_repository']=='maichicong835/A-Ver'
assert c['canonical_branch']=='main'
assert c['daily7_live_gate_authorized'] is False
assert c['acceptance_snapshot']['G5_DAILY7_DEEP_SHADOW']=='PASS_CLOSED_DAILY7_MAIN_G5_REPROOF_34788711694'
assert c['acceptance_snapshot']['G6_LIVE_BOUNDARY_REHEARSAL']=='PASS_CLOSED_DAILY7_MAIN_G6_REHEARSAL_34788711694'
assert c['acceptance_snapshot']['G6B_PRODUCTION_INVOCATION_REACHABILITY']=='PASS_CLOSED_DAILY7_MAIN_G6B_PRODUCTION_INVOCATION_34788711694'
assert c['current_reopen_scope']['only_layer']=='LIVE_READINESS_GOVERNOR_RECEIPT'
assert c['current_reopen_scope']['next_machine_gate']=='RUN_GOVERNOR_EXPECT_READY_THEN_G7_EXPLICIT_AUTHORIZATION'
assert e['acceptance']['daily7_deep_shadow_g5']['status']=='PASS_CLOSED_DAILY7_MAIN_G5_REPROOF_34788711694'
assert e['acceptance']['live_boundary_rehearsal_g6']['status']=='PASS_CLOSED_DAILY7_MAIN_G6_REHEARSAL_34788711694'
assert e['acceptance']['production_invocation_g6b']['status']=='PASS_CLOSED_DAILY7_MAIN_G6B_PRODUCTION_INVOCATION_34788711694'
assert e['production_transition']['g6_live_boundary_rehearsal_passed'] is True
assert e['production_transition']['g6b_production_invocation_passed'] is True
assert e['production_transition']['daily7_live_gate_authorized'] is False
assert s['live_authorized'] is False

g5=s['daily7_deep_shadow_closure']
g6=s['live_boundary_rehearsal_closure']
g6b=s['production_invocation_closure']
for closure in [g5,g6,g6b]:
    assert closure['state']=='PASS_CLOSED'
    assert closure['aver_pin_sha']==PIN
    assert str(closure['workflow_run_id'])==DAILY7_PROOF_RUN
    assert str(closure['artifact_id'])==ARTIFACT
    assert closure['artifact_digest']==DIGEST

assert g5['daily7_execution_head_sha']==DAILY7_HEAD
assert g5['daily7_current_clean_head_sha']==DAILY7_HEAD
assert str(g5['daily7_repo_guard_run_id'])==DAILY7_GUARD_RUN
assert g5['daily7_repo_guard_conclusion']=='success'
assert g5['caller_mutation_observed'] is False
assert g5['drive_mutation_observed'] is False
assert g5['used_reserve_mutation_observed'] is False
assert g5['false_tm_pass_observed'] is False
assert g5['false_tm_kill_observed'] is False

assert g6['daily7_head_sha']==DAILY7_HEAD
assert str(g6['daily7_repo_guard_run_id'])==DAILY7_GUARD_RUN
assert g6['daily7_repo_guard_conclusion']=='success'
assert g6['mutation_enabled'] is False
assert g6['pass_kill_hold_handling_proven'] is True
assert g6['fail_closed_boundary_proven'] is True
assert g6['live_without_explicit_authorization_blocked'] is True
assert g6['g7_authorized'] is False

assert g6b['daily7_head_sha']==DAILY7_HEAD
assert str(g6b['daily7_repo_guard_run_id'])==DAILY7_GUARD_RUN
assert g6b['daily7_repo_guard_conclusion']=='success'
assert g6b['generic_entrypoint_machine_proven'] is True
assert g6b['request_schema_validated'] is True
assert g6b['receipt_schema_validated'] is True
assert g6b['arbitrary_unproven_scope_fails_closed'] is True
assert g6b['daily7_caller_exact_pin_invocation_proven'] is True
assert g6b['same_g6_router_used'] is True
assert g6b['primary_actual_decision']=='TM_PASS'
assert g6b['failclosed_actual_decision']=='TM_HOLD'
assert g6b['daily7_state_mutation_observed'] is False
assert g6b['drive_mutation_observed'] is False
assert g6b['used_reserve_mutation_observed'] is False

assert s['g7_explicit_live_authorization']['state']=='AWAITING_EXPLICIT_USER_AUTHORIZATION_AFTER_G1_G6B_READY'
assert s['g7_explicit_live_authorization']['owned_by']=='DAILY7_CALLER_GOVERNANCE'
print('AVER_CONTRACT_TEST_G6B_MAIN_CLOSURE_PASS')
