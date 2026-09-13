#!/usr/bin/env python3
import json
from pathlib import Path

from aver.decision import evaluate_tm_state
from aver.interpretation import g0_g4, lexical_materiality

FIXTURE = Path('tests/fixtures/record-binding-34735150433.json')
OUT = Path('artifacts/deep-shadow-reassess')
OUT.mkdir(parents=True, exist_ok=True)


def main():
    fixture = json.loads(FIXTURE.read_text(encoding='utf-8'))
    receipt = {
        'schema': 'AVER_DEEP_SHADOW_REASSESSMENT_RECEIPT',
        'source': fixture['source'],
        'fixture_only_not_runtime_authority': True,
        'caller_state_mutation_authorized': False,
        'drive_mutation_authorized': False,
        'live_gate_authorized': False,
        'records': [],
    }
    for rec in fixture['records']:
        lexical = lexical_materiality(rec['candidate_wording'], rec['mark_text'])
        goods_text = '; '.join(rec.get('goods_markers') or [])
        goods = g0_g4(goods_text, rec.get('class_codes') or [])
        final_goods = 'MATERIAL' if goods['bucket'] == 'G0' else 'UNRESOLVED'
        final_similarity = 'UNRESOLVED'
        state = {
            'material_positive_record_present': True,
            'record_binding_complete': rec['record_binding_state'] == 'RECORD_BINDING_PASS',
            'similarity_assessment': final_similarity,
            'goods_relatedness_assessment': final_goods,
            'required_query_dimensions_complete': False,
            'resolver_scope_complete': False,
            'unresolved_dimensions': [
                'EXACT',
                'NORMALIZED_EXACT',
                'CORE_DOMINANT_TOKEN',
                'EXPANDED_PARTIAL',
                'PHONETIC_OR_SPELLING_WHEN_MATERIAL',
                'RELATED_GOODS_REVIEW',
                'FINAL_SIMILARITY',
            ],
            'negative_evidence_distinct_sources': 0,
            'transport_blocked': False,
            'control_blocked': False,
            'source_discordance': False,
        }
        decision = evaluate_tm_state(state)
        receipt['records'].append({
            **rec,
            'lexical_similarity_triage': lexical,
            'g0_g4_reassessment': goods,
            'final_similarity': final_similarity,
            'final_goods_relatedness': final_goods,
            'decision': decision,
            'exact_dimension_resolved': False,
            'required_query_scope_complete': False,
        })

    if any(x['decision']['decision'] != 'TM_HOLD' for x in receipt['records']):
        raise SystemExit('DEEP_REASSESS_FALSE_NON_HOLD')
    nursing = next(x for x in receipt['records'] if x['serial'] == '90319838')
    chaos = next(x for x in receipt['records'] if x['serial'] == '90072046')
    if nursing['g0_g4_reassessment']['bucket'] != 'G0':
        raise SystemExit('NURSING_RECORD_NOT_G0_AFTER_DETAIL_BINDING')
    if chaos['g0_g4_reassessment']['bucket'] != 'G3':
        raise SystemExit('CHAOS_RECORD_NOT_G3')
    receipt['phase_state'] = 'RECORD_DETAIL_AND_G0_G4_REASSESSMENT_PASS_SIMILARITY_AND_SCOPE_HOLD'
    receipt['next_machine_gate'] = 'SIMILARITY_COMMERCIAL_IMPRESSION_AND_REMAINING_REQUIRED_QUERY_SCOPE'
    (OUT / 'reassessment.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('AVER_DEEP_SHADOW_REASSESSMENT_PASS')
    for x in receipt['records']:
        print(x['serial'], x['g0_g4_reassessment']['bucket'], x['final_similarity'], x['decision']['decision'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
