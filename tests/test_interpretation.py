#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path('src')))
from aver.interpretation import g0_g4, lexical_materiality, materiality_priority

nursing = 'I KNOW THEY SAID NURSING SCHOOL WAS HARD, BUT DAMN'
lex = lexical_materiality(nursing, 'NURSING SCHOOL JEWELS')
goods = g0_g4('Notebooks; flash cards; notebook covers; stationery', ['016'])
assert lex['state'] == 'WEAK_TOKEN_OVERLAP'
assert set(lex['overlap_tokens']) == {'nursing', 'school'}
assert goods['bucket'] == 'G1'
assert materiality_priority(lex, goods) == 'P2_REVIEW_IF_SCOPE_REMAINS_UNRESOLVED'
assert lex['final_similarity_decision'] == 'UNRESOLVED'
assert goods['final_goods_relatedness'] == 'UNRESOLVED'

powered = 'POWERED BY YARN AND CHAOS'
lex2 = lexical_materiality(powered, 'CHAOS BY ELSIE')
goods2 = g0_g4('Handbags', ['018'])
assert lex2['state'] == 'WEAK_TOKEN_OVERLAP'
assert lex2['overlap_tokens'] == ['chaos']
assert goods2['bucket'] == 'G3'
assert materiality_priority(lex2, goods2) == 'P2_REVIEW_IF_SCOPE_REMAINS_UNRESOLVED'

noise = lexical_materiality(powered, 'POWERED BY P')
noise_goods = g0_g4('Semiconductors; integrated circuits; electronic components', ['007', '009'])
assert noise['state'] == 'WEAK_TOKEN_OVERLAP'
assert noise_goods['bucket'] == 'G4'
assert materiality_priority(noise, noise_goods) == 'P3_LOW_PRIORITY_FUZZY_NOISE'

exact = lexical_materiality('HELLO WORLD', 'hello world')
assert exact['state'] == 'EXACT_NORMALIZED_MATCH'
assert materiality_priority(exact, g0_g4('Stickers', ['016'])) == 'P0_RECORD_DETAIL_REQUIRED'

print('AVER_INTERPRETATION_TEST_PASS')
