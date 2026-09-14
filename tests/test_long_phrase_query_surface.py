#!/usr/bin/env python3
from aver.production import grammar_ok
from aver.query_plan import STOPWORDS, build_query_plan

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
        toks=core.split()
        assert all(len(tok)>1 or tok.isdigit() for tok in toks), (phrase,core)
        if len(toks)>1:
            assert toks[0] not in STOPWORDS and toks[-1] not in STOPWORDS, (phrase,core)

silent_plan=build_query_plan("I'M SILENTLY CREATING A SPREADSHEET FOR THAT",[])
silent_cores=silent_plan["CORE_DOMINANT_TOKEN"]["queries"]
assert all(" M " not in f" {core} " for core in silent_cores), silent_cores
assert "SILENTLY CREATING SPREADSHEET" in silent_cores, silent_cores
assert "CREATING SPREADSHEET" in silent_cores, silent_cores
assert all(not core.endswith(" FOR") for core in silent_cores), silent_cores
print("AVER_LONG_PHRASE_BOUNDED_CORE_CONTRACT_PASS")
