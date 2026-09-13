#!/usr/bin/env python3
import json
from pathlib import Path

from aver.record_binding import bind_trademarkia_record

OUT = Path('artifacts/deep-shadow-record-binding')
OUT.mkdir(parents=True, exist_ok=True)
TARGETS = [
    {
        'candidate_key': 'nursing-school-hard-but-damn',
        'serial': '90319838',
        'mark_text': 'NURSING SCHOOL JEWELS',
        'expected_class': '016',
    },
    {
        'candidate_key': 'powered-by-yarn-and-chaos',
        'serial': '90072046',
        'mark_text': 'CHAOS BY ELSIE',
        'expected_class': '018',
    },
]


def main():
    receipt = {
        'schema': 'AVER_DEEP_SHADOW_RECORD_BINDING_RECEIPT',
        'target_scope': 'EXACTLY_TWO_INTERPRETATION_SURVIVOR_RECORDS',
        'new_candidate_discovery_executed': False,
        'caller_state_mutation_authorized': False,
        'drive_mutation_authorized': False,
        'live_gate_authorized': False,
        'records': [],
    }
    for target in TARGETS:
        bound = bind_trademarkia_record(target['mark_text'], target['serial'])
        bound['candidate_key'] = target['candidate_key']
        bound['expected_class'] = target['expected_class']
        bound['expected_class_seen'] = target['expected_class'] in bound.get('class_codes', [])
        if bound['state'] == 'RECORD_BINDING_PASS' and not bound['expected_class_seen']:
            bound['state'] = 'RECORD_BINDING_INCOMPLETE'
            bound['failure_signature'] = 'EXPECTED_CLASS_NOT_BOUND'
        receipt['records'].append(bound)

    passes = sum(1 for x in receipt['records'] if x['state'] == 'RECORD_BINDING_PASS')
    receipt['binding_pass_count'] = passes
    receipt['binding_target_count'] = len(TARGETS)
    receipt['phase_state'] = 'RECORD_DETAIL_BINDING_PASS' if passes == len(TARGETS) else 'RECORD_DETAIL_BINDING_PARTIAL_HOLD'
    receipt['tm_decision'] = 'TM_HOLD'
    receipt['decision_reason_codes'] = [
        'RECORD_BINDING_DOES_NOT_COMPLETE_SIMILARITY_ANALYSIS',
        'RECORD_BINDING_DOES_NOT_COMPLETE_RELATED_GOODS_REVIEW',
        'REQUIRED_QUERY_SCOPE_REMAINS_INCOMPLETE',
    ]
    if passes != len(TARGETS):
        receipt['decision_reason_codes'].insert(0, 'ONE_OR_MORE_RECORD_DETAILS_NOT_MACHINE_BOUND')

    (OUT / 'record-binding.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('AVER_DEEP_SHADOW_RECORD_BINDING_PASS' if passes == len(TARGETS) else 'AVER_DEEP_SHADOW_RECORD_BINDING_PARTIAL_HOLD')
    for x in receipt['records']:
        print(x['candidate_key'], x['serial'], x['state'], 'classes=', ','.join(x.get('class_codes') or []), 'status=', ','.join(x.get('status_tokens') or []))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
