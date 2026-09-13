#!/usr/bin/env python3
from aver.query_plan import build_query_plan

phrase="Mildly Lost, Weirdly Optimistic"
plan=build_query_plan(phrase,[])

assert plan["required_dimensions"]==[
    "EXACT","NORMALIZED_EXACT","CORE_DOMINANT_TOKEN","EXPANDED_PARTIAL",
    "PHONETIC_OR_SPELLING_WHEN_MATERIAL","RELATED_GOODS_REVIEW"
]
cores=plan["CORE_DOMINANT_TOKEN"]["queries"]
assert len(cores)==2
assert all(cores)
assert all(x["source"].startswith("DETERMINISTIC_CLEAN_PATH") for x in plan["CORE_DOMINANT_TOKEN"]["derivation"])
assert plan["EXPANDED_PARTIAL"]["queries"]==cores
phon=plan["PHONETIC_OR_SPELLING_WHEN_MATERIAL"]
assert phon["state"]=="REQUIRED_BOUNDED_USPTO_REGEX"
assert len(phon["queries"])==1
assert phon["queries"][0].startswith("CM:(/")
assert phon["negative_semantics_required"]=="USPTO_NATIVE_ZERO_FOR_BOUND_REGEX"
assert plan["RELATED_GOODS_REVIEW"]["state"]=="BOUND_RESULTSET_GOODS_REVIEW_REQUIRED"
assert plan["legal_clearance_asserted"] is False
print("AVER_NEGATIVE_PATH_QUERY_PLAN_PASS")
