#!/usr/bin/env python3
from aver.production import grammar_ok
from aver.query_plan import build_query_plan

PHRASES=[
    "MAYBE WITH ENOUGH SPREADSHEETS LIFE WILL MAKE SENSE",
    "I'M SILENTLY CREATING A SPREADSHEET FOR THAT",
]

for phrase in PHRASES:
    assert not grammar_ok(phrase)
    cores=build_query_plan(phrase,[])["CORE_DOMINANT_TOKEN"]["queries"]
    assert cores
    assert all(grammar_ok(core) for core in cores), (phrase,cores)

print("AVER_LONG_PHRASE_CURRENT_GATE_REPRODUCED")
