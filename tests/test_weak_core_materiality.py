#!/usr/bin/env python3
from aver.production import pq, _weak_core_context_tokens, _weak_core_shape, _direct_sticker_goods_overlap

assert pq("CAN LEAVE AMA") == "CM:(/.*leave.*/) AND CM:CAN AND CM:AMA"
assert pq("ANXIETY IS MY") == "CM:(/.*anxiety.*/) AND CM:IS AND CM:MY"

w="FOR THE LAST TIME, YOU CAN'T LEAVE AMA YOU WORK HERE"
core="LAST TIME"
mark="HOW TO LOSE WEIGHT FOR THE LAST TIME"
shape=_weak_core_shape(w,core,mark)
assert shape["shared_outside_core"]==[]
assert shape["candidate_overlap_ratio"] <= 0.40
assert shape["record_overlap_ratio"] <= 0.50
assert _weak_core_context_tokens(w,core,2)==["leave","work"]

req={"intended_goods_context":{"description":"Printed vinyl stickers and decals for laptops and water bottles"}}
book_detail={"goods_services_excerpt":"IC 016: Blank journal books; Printed educational materials in the field of life and weight loss coaching"}
sticker_detail={"goods_services_excerpt":"IC 016: Printed stickers; decals; adhesive labels"}
assert _direct_sticker_goods_overlap(req,book_detail) is False
assert _direct_sticker_goods_overlap(req,sticker_detail) is True
print("AVER_WEAK_CORE_MATERIALITY_UNIT_PASS")
