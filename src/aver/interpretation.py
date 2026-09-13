#!/usr/bin/env python3
import re

STOPWORDS = {
    'a','an','and','are','as','at','be','but','by','for','from','i','in','is','it','of','on','or','the','they','to','was','we','with'
}


def normalize_words(text):
    return re.findall(r"[a-z0-9]+", (text or '').lower())


def distinctive_tokens(text):
    return [t for t in normalize_words(text) if t not in STOPWORDS and len(t) > 2]


def lexical_materiality(query, mark):
    q = distinctive_tokens(query)
    m = distinctive_tokens(mark)
    qset, mset = set(q), set(m)
    overlap = sorted(qset & mset)
    exact = normalize_words(query) == normalize_words(mark)
    query_contains_mark = bool(m) and ' '.join(m) in ' '.join(q)
    mark_contains_query = bool(q) and ' '.join(q) in ' '.join(m)
    ratio = len(overlap) / max(1, len(qset))
    if exact:
        state = 'EXACT_NORMALIZED_MATCH'
    elif len(overlap) >= 2 and (ratio >= 0.5 or query_contains_mark or mark_contains_query):
        state = 'POTENTIALLY_MATERIAL_CORE_OVERLAP'
    elif overlap:
        state = 'WEAK_TOKEN_OVERLAP'
    else:
        state = 'NO_LEXICAL_OVERLAP'
    return {
        'state': state,
        'query_tokens': q,
        'mark_tokens': m,
        'overlap_tokens': overlap,
        'query_overlap_ratio': round(ratio, 4),
        'final_similarity_decision': 'UNRESOLVED',
    }


def g0_g4(goods_text, class_codes):
    text = (goods_text or '').lower()
    classes = {str(x).zfill(3) for x in (class_codes or [])}
    sticker_terms = ('sticker','stickers','decal','decals','adhesive label','printed sticker')
    print_terms = ('notebook','stationery','printed','paper','poster','journal','flash card','publication')
    apparel_terms = ('shirt','shirts','t-shirt','clothing','apparel','hoodie','hat','cap')
    if '016' in classes and any(x in text for x in sticker_terms):
        bucket = 'G0'
        rationale = 'CLASS016_EXACT_OR_NEAR_STICKER_GOODS'
    elif '016' in classes and any(x in text for x in print_terms):
        bucket = 'G1'
        rationale = 'CLASS016_PRINTED_OR_STATIONERY_RELATED_GOODS'
    elif '025' in classes or any(x in text for x in apparel_terms):
        bucket = 'G2'
        rationale = 'COORDINATED_APPAREL_OR_MERCH_ADJACENCY'
    elif classes & {'018','021','024','026','028'}:
        bucket = 'G3'
        rationale = 'CONSUMER_MERCH_ADJACENCY_WITHOUT_DIRECT_CLASS016_MATCH'
    else:
        bucket = 'G4'
        rationale = 'NO_OBSERVED_DIRECT_OR_COORDINATED_GOODS_MATCH'
    return {'bucket': bucket, 'rationale': rationale, 'final_goods_relatedness': 'UNRESOLVED'}


def materiality_priority(lexical, goods):
    lstate = lexical['state']
    bucket = goods['bucket']
    if lstate == 'EXACT_NORMALIZED_MATCH':
        return 'P0_RECORD_DETAIL_REQUIRED'
    if lstate == 'POTENTIALLY_MATERIAL_CORE_OVERLAP' and bucket in {'G0','G1','G2'}:
        return 'P1_RECORD_DETAIL_REQUIRED'
    if lstate in {'POTENTIALLY_MATERIAL_CORE_OVERLAP','WEAK_TOKEN_OVERLAP'} and bucket in {'G0','G1','G2','G3'}:
        return 'P2_REVIEW_IF_SCOPE_REMAINS_UNRESOLVED'
    return 'P3_LOW_PRIORITY_FUZZY_NOISE'
