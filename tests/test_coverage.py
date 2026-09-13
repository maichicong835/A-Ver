#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path('src')))
from aver.coverage import plan_scope

p = plan_scope('016', ['025'], 'MULTI_TOKEN')
assert p['primary_class'] == '016'
assert p['negative_pass_capable'] is False
assert p['tm_kill_capable_from_material_positive'] is True
assert p['tm_hold_capable'] is True
assert p['distinct_negative_source_count'] == 0
assert 'CLASS016_MULTI_TOKEN_EXACT_NEGATIVE_SEMANTICS_UNPROVEN' in p['structural_blockers']
assert 'SECOND_DISTINCT_PRIMARY_CLASS_NEGATIVE_SOURCE_MISSING' in p['structural_blockers']
assert 'REQUIRED_QUERY_DIMENSIONS_NOT_NEGATIVELY_RESOLVABLE_WITH_CURRENT_PROFILE' in p['structural_blockers']
assert 'RELATED_GOODS_REVIEW' not in p['unresolved_query_dimensions']
assert {'EXACT','NORMALIZED_EXACT'}.issubset(set(p['unresolved_query_dimensions']))
assert p['probability_or_search_miss_may_not_fill_gap'] is True
assert p['resultset_positive_may_not_be_reinterpreted_as_negative_scope_coverage'] is True

# IC025 has proven TMHunt negative semantics but still only one class-relevant source.
p25 = plan_scope('025', [], 'MULTI_TOKEN')
assert p25['negative_pass_capable'] is False
assert p25['distinct_negative_source_count'] == 1
assert p25['class_relevant_negative_sources'] == ['TMHUNT_IC025']
assert 'SECOND_DISTINCT_PRIMARY_CLASS_NEGATIVE_SOURCE_MISSING' in p25['structural_blockers']

print('AVER_COVERAGE_PLANNER_TEST_PASS')
