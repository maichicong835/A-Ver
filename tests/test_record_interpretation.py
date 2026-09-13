#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

from aver.record_interpretation import bind_record_anchor

fixture = json.loads(Path('tests/fixtures/daily7_shadow_record_contexts.json').read_text(encoding='utf-8'))
assert fixture['source']['workflow_run_id'] == '34722878035'
assert fixture['source']['artifact_id'] == '10306408819'
assert fixture['source']['artifact_digest'] == 'sha256:7251ad40baf0fad95f348419cd84d24b2cc1fd23d176e1c4d2690ccf640aa036'

for item in fixture['canaries']:
    body = item['body_excerpt']
    assert hashlib.sha256(body.encode()).hexdigest() == item['fixture_context_sha256']
    bound = bind_record_anchor(body, item['mark_text'], item['serial'], item['expected_class'])
    assert bound['bound'] is True, item['candidate_key']
    assert bound['identifier'] == item['serial']
    assert item['expected_class'] in bound['classes']
    assert bound['status'].lower().startswith('live/registered')

nursing = fixture['canaries'][0]
wrong_class = bind_record_anchor(nursing['body_excerpt'], nursing['mark_text'], nursing['serial'], '025')
assert wrong_class['bound'] is False
assert wrong_class['failure_signature'] == 'EXPECTED_CLASS_NOT_BOUND'

yarn = fixture['canaries'][1]
wrong_mark = bind_record_anchor(yarn['body_excerpt'], 'POWERED BY YARN AND CHAOS', yarn['serial'], yarn['expected_class'])
assert wrong_mark['bound'] is False
assert wrong_mark['failure_signature'] in {'MARK_CROSSES_RESULT_HEADER', 'MARK_TOO_FAR_FROM_SERIAL'}

print('AVER_RECORD_INTERPRETATION_TEST_PASS')
