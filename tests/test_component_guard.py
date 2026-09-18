#!/usr/bin/env python3
from aver.production import _independent_component_candidates, _body_has_exact_live_wordmark

wording="FOR THE LAST TIME, YOU CAN'T LEAVE AMA YOU WORK HERE"
cores={"LAST TIME"}
assert _independent_component_candidates(wording,cores,limit=3)==["ama","leave"], _independent_component_candidates(wording,cores,limit=3)
rec={"body_excerpt":"Wordmark wordmark AMA Status LIVEREGISTERED Goods & services IC 016: Printed publications"}
assert _body_has_exact_live_wordmark(rec,"ama") is True
assert _body_has_exact_live_wordmark(rec,"leave") is False
print("AVER_COMPONENT_GUARD_UNIT_PASS")
