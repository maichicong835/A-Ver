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
            'positive_discovery_capabilities': [],
            'negative_semantics_capabilities': [],
            'dimension_can_be_fully_resolved_negative_today': False,
        }
        if dim in {'EXACT','NORMALIZED_EXACT','CORE_DOMINANT_TOKEN','EXPANDED_PARTIAL','PHONETIC_OR_SPELLING_WHEN_MATERIAL'}:
            entry['positive_discovery_capabilities'].append('TRADEMARKIA_BROAD_FEDERAL_RECALL')
        if dim == 'RELATED_GOODS_REVIEW':
            entry['positive_discovery_capabilities'].append('BOUND_RECORD_CLASS_AND_GOODS_CONTEXT')
            entry['dimension_can_be_fully_resolved_negative_today'] = True

        if primary == '025':
            if dim in {'EXACT','NORMALIZED_EXACT'}:
                entry['negative_semantics_capabilities'].append('TMHUNT_EXACT_ZERO_IC025')
                entry['dimension_can_be_fully_resolved_negative_today'] = True
            elif dim in {'CORE_DOMINANT_TOKEN','EXPANDED_PARTIAL'}:
                entry['negative_semantics_capabilities'].append('TMHUNT_PARTIAL_IC025_DISCOVERY_ONLY')

        if wording_kind == 'OPAQUE_SINGLE_TOKEN' and dim in {'EXACT','NORMALIZED_EXACT'}:
            entry['negative_semantics_capabilities'].append('TRADEMARKIA_OPAQUE_SINGLE_TOKEN_ZERO_LIMITED')
            if primary != '016':
                entry['dimension_can_be_fully_resolved_negative_today'] = True

        coverage.append(entry)

    unresolved_dimensions = [x['dimension'] for x in coverage if not x['dimension_can_be_fully_resolved_negative_today']]
    class_relevant_negative_sources = []
    if primary == '025':
        class_relevant_negative_sources.append('TMHUNT_IC025')
    if wording_kind == 'OPAQUE_SINGLE_TOKEN':
        class_relevant_negative_sources.append('TRADEMARKIA_OPAQUE_ZERO_LIMITED')

    blockers = []
    if primary == '016' and wording_kind == 'MULTI_TOKEN':
        blockers.append('CLASS016_MULTI_TOKEN_EXACT_NEGATIVE_SEMANTICS_UNPROVEN')
    if len(set(class_relevant_negative_sources)) < 2:
        blockers.append('SECOND_DISTINCT_PRIMARY_CLASS_NEGATIVE_SOURCE_MISSING')
    if unresolved_dimensions:
        blockers.append('REQUIRED_QUERY_DIMENSIONS_NOT_NEGATIVELY_RESOLVABLE_WITH_CURRENT_PROFILE')

    return {
        'primary_class': primary,
        'coordinated_classes': sorted(coordinated),
        'wording_kind': wording_kind,
        'required_dimensions': REQUIRED_DIMENSIONS,
        'coverage': coverage,
        'class_relevant_negative_sources': sorted(set(class_relevant_negative_sources)),
        'distinct_negative_source_count': len(set(class_relevant_negative_sources)),
        'negative_pass_capable': not blockers,
        'tm_kill_capable_from_material_positive': True,
        'tm_hold_capable': True,
        'unresolved_query_dimensions': unresolved_dimensions,
        'structural_blockers': blockers,
        'probability_or_search_miss_may_not_fill_gap': True,
        'resultset_positive_may_not_be_reinterpreted_as_negative_scope_coverage': True,
    }
