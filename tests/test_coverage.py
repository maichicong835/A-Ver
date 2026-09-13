#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path('src')))
from aver.coverage import plan_scope

p = plan_scope('016', ['025'], 'MULTI_TOKEN')
assert p['primary_class'] == '016'
assert p['negative_pass_capable'] is False
assert p['structural_blocker'] == 'PRIMARY_CLASS_NEGATIVE_CONVERGENCE_CAPABILITY_INCOMPLETE'
assert p['tm_kill_capable_from_material_positive'] is True
assert p['tm_hold_capable'] is True
assert set(p['unresolved_negative_dimensions']) == {
    'EXACT','NORMALIZED_EXACT','CORE_DOMINANT_TOKEN','EXPANDED_PARTIAL',
    'PHONETIC_OR_SPELLING_WHEN_MATERIAL','RELATED_GOODS_REVIEW'
}
assert p['probability_or_search_miss_may_not_fill_gap'] is True

# Even IC025 has only one proven negative resolver family today; do not invent convergence.
p25 = plan_scope('025', [], 'MULTI_TOKEN')
assert p25['negative_pass_capable'] is False
assert p25['structural_blocker'] == 'PRIMARY_CLASS_NEGATIVE_CONVERGENCE_CAPABILITY_INCOMPLETE'

print('AVER_COVERAGE_PLANNER_TEST_PASS')
