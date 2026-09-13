#!/usr/bin/env python3

REQUIRED_DIMENSIONS = [
    'EXACT',
    'NORMALIZED_EXACT',
    'CORE_DOMINANT_TOKEN',
    'EXPANDED_PARTIAL',
    'PHONETIC_OR_SPELLING_WHEN_MATERIAL',
    'RELATED_GOODS_REVIEW',
]


def plan_scope(primary_class, coordinated_classes=None, wording_kind='MULTI_TOKEN'):
    primary = str(primary_class).zfill(3)
    coordinated = {str(x).zfill(3) for x in (coordinated_classes or [])}
    coverage = []

    for dim in REQUIRED_DIMENSIONS:
        entry = {
            'dimension': dim,
            'positive_discovery': [],
            'negative_evidence': [],
            'negative_scope_complete_for_primary_class': False,
        }
        if dim in {'EXACT','NORMALIZED_EXACT','CORE_DOMINANT_TOKEN','EXPANDED_PARTIAL','PHONETIC_OR_SPELLING_WHEN_MATERIAL'}:
            entry['positive_discovery'].append('TRADEMARKIA_BROAD_FEDERAL_RECALL')
        if dim == 'RELATED_GOODS_REVIEW':
            entry['positive_discovery'].append('BOUND_RECORD_CLASS_AND_GOODS_CONTEXT')

        if primary == '025':
            if dim in {'EXACT','NORMALIZED_EXACT'}:
                entry['negative_evidence'].append('TMHUNT_EXACT_ZERO_IC025')
            if dim in {'CORE_DOMINANT_TOKEN','EXPANDED_PARTIAL'}:
                entry['negative_evidence'].append('TMHUNT_PARTIAL_IC025')

        if wording_kind == 'OPAQUE_SINGLE_TOKEN' and dim in {'EXACT','NORMALIZED_EXACT'}:
            entry['negative_evidence'].append('TRADEMARKIA_OPAQUE_SINGLE_TOKEN_ZERO_LIMITED')

        if primary == '025' and len(set(entry['negative_evidence'])) >= 2:
            entry['negative_scope_complete_for_primary_class'] = True
        coverage.append(entry)

    unresolved_negative = [x['dimension'] for x in coverage if not x['negative_scope_complete_for_primary_class']]
    pass_capable = not unresolved_negative
    return {
        'primary_class': primary,
        'coordinated_classes': sorted(coordinated),
        'wording_kind': wording_kind,
        'required_dimensions': REQUIRED_DIMENSIONS,
        'coverage': coverage,
        'negative_pass_capable': pass_capable,
        'tm_kill_capable_from_material_positive': True,
        'tm_hold_capable': True,
        'unresolved_negative_dimensions': unresolved_negative,
        'structural_blocker': None if pass_capable else 'PRIMARY_CLASS_NEGATIVE_CONVERGENCE_CAPABILITY_INCOMPLETE',
        'probability_or_search_miss_may_not_fill_gap': True,
    }
