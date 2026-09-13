#!/usr/bin/env python3
import json
from pathlib import Path

from aver.interpretation import g0_g4, lexical_materiality, materiality_priority

FIXTURE = Path('tests/fixtures/shadow-34722878035-top-records.json')
OUT = Path('artifacts/deep-shadow')
OUT.mkdir(parents=True, exist_ok=True)


def main():
    fixture = json.loads(FIXTURE.read_text(encoding='utf-8'))
    output = {
        'schema': 'AVER_DEEP_SHADOW_INTERPRETATION_RECEIPT',
        'source_fixture': fixture['source'],
        'fixture_only_not_runtime_authority': True,
        'caller_state_mutation_authorized': False,
        'drive_mutation_authorized': False,
        'live_gate_authorized': False,
        'subgate_state': 'RESULT_ROW_INTERPRETATION_PASS',
        'phase_state': 'SHADOW_DEEP_TM_INTERPRETATION_HOLD_RECORD_DETAIL_AND_SCOPE',
        'canaries': [],
    }

    for canary in fixture['canaries']:
        rows = []
        follow_up = []
        for row in canary['rows']:
            lexical = lexical_materiality(canary['wording'], row['mark_text'])
            goods = g0_g4(row['goods_excerpt'], row['class_codes'])
            priority = materiality_priority(lexical, goods)
            interpreted = {
                **row,
                'lexical_materiality': lexical,
                'g0_g4': goods,
                'follow_up_priority': priority,
                'record_detail_bound': False,
                'final_similarity': 'UNRESOLVED',
                'final_goods_relatedness': 'UNRESOLVED',
            }
            rows.append(interpreted)
            if priority != 'P3_LOW_PRIORITY_FUZZY_NOISE':
                follow_up.append({
                    'serial': row['serial'],
                    'mark_text': row['mark_text'],
                    'priority': priority,
                    'reason': [lexical['state'], goods['bucket']],
                })

        output['canaries'].append({
            'candidate_key': canary['candidate_key'],
            'wording': canary['wording'],
            'rows_interpreted': rows,
            'record_detail_follow_up': follow_up,
            'tm_decision': 'TM_HOLD',
            'decision_reason_codes': [
                'RECORD_DETAIL_BINDING_INCOMPLETE',
                'FINAL_SIMILARITY_UNRESOLVED',
                'FINAL_GOODS_RELATEDNESS_UNRESOLVED',
                'REQUIRED_QUERY_SCOPE_INCOMPLETE',
            ],
            'exact_dimension_resolved': False,
            'broad_fuzzy_resultset_may_not_resolve_exact_dimension': True,
        })

    if len(output['canaries']) != 2:
        raise SystemExit('DEEP_SHADOW_CANARY_COUNT_MISMATCH')
    if any(x['tm_decision'] != 'TM_HOLD' for x in output['canaries']):
        raise SystemExit('DEEP_SHADOW_FALSE_DECISION')
    if any(x['exact_dimension_resolved'] for x in output['canaries']):
        raise SystemExit('DEEP_SHADOW_FALSE_EXACT_COVERAGE')

    target = OUT / 'deep-interpretation.json'
    target.write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    print('AVER_DEEP_SHADOW_INTERPRETATION_PASS')
    for x in output['canaries']:
        print(x['candidate_key'], 'TM_HOLD', 'follow_up=', len(x['record_detail_follow_up']))
        for f in x['record_detail_follow_up']:
            print(' ', f['serial'], f['mark_text'], f['priority'], ','.join(f['reason']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
