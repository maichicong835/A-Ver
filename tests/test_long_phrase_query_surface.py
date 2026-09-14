#!/usr/bin/env python3
from aver.production import grammar_ok
from aver.query_plan import build_query_plan

PHRASES=[
    "MAYBE WITH ENOUGH SPREADSHEETS LIFE WILL MAKE SENSE",
    "I'M SILENTLY CREATING A SPREADSHEET FOR THAT",
]

for phrase in PHRASES:
    assert not grammar_ok(phrase), "full phrase should not be forced into bounded core grammar"
    cores=build_query_plan(phrase,[])["CORE_DOMINANT_TOKEN"]["queries"]
    assert cores
    assert all(grammar_ok(core) for core in cores), (phrase,cores)
    for core in cores:
        assert all(len(tok)>1 or tok.isdigit() for tok in core.split()), (phrase,core)

silent_cores=build_query_plan("I'M SILENTLY CREATING A SPREADSHEET FOR THAT",[])["CORE_DOMINANT_TOKEN"]["queries"]
assert all(" M " not in f" {core} " for core in silent_cores), silent_cores
print("AVER_LONG_PHRASE_BOUNDED_CORE_CONTRACT_PASS")
