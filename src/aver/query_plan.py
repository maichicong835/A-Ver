#!/usr/bin/env python3
import re

REQUIRED_DIMENSIONS = [
    "EXACT",
    "NORMALIZED_EXACT",
    "CORE_DOMINANT_TOKEN",
    "EXPANDED_PARTIAL",
    "PHONETIC_OR_SPELLING_WHEN_MATERIAL",
    "RELATED_GOODS_REVIEW",
]

STOPWORDS={"A","AN","AND","ARE","AS","AT","BE","BY","FOR","FROM","I","IN","IS","IT","OF","ON","OR","THE","TO","WE","WITH","YOU"}


def _tokens(value):
    return re.findall(r"[a-z0-9]+", (value or "").lower())


def normalize_wording(value):
    return " ".join(_tokens(value)).upper()


def _surface_upper(value):
    return re.sub(r"\s+", " ", (value or "").strip()).upper()


def _longest_contiguous_shared(a, b):
    best=[]
    for i in range(len(a)):
        for j in range(len(b)):
            k=0
            while i+k < len(a) and j+k < len(b) and a[i+k]==b[j+k]:
                k+=1
            if k>len(best):
                best=a[i:i+k]
    return best


def derive_core_queries(candidate_wording, priority_queue, limit=2):
    """Derive bounded cores from bound material records when available."""
    c=_tokens(candidate_wording)
    candidates=[]
    seen=set()
    for rank,item in enumerate(priority_queue or []):
        shared=_longest_contiguous_shared(c,_tokens(item.get("mark_text")))
        if not shared:
            continue
        q=" ".join(shared).upper()
        if q in seen:
            continue
        seen.add(q)
        candidates.append({
            "query":q,
            "token_count":len(shared),
            "source":"MATERIAL_RECORD_OVERLAP",
            "source_record_identifier":item.get("identifier"),
            "source_record_priority":item.get("priority_score",0),
            "source_rank":rank+1,
        })
    candidates.sort(key=lambda x:(-x["token_count"],-x["source_record_priority"],x["source_rank"],x["query"]))
    return candidates[:limit]


def derive_fallback_core_queries(candidate_wording, limit=2):
    """Deterministic clean-path cores when no material record provides overlap.

    We use contiguous 2-3 token n-grams, prefer more non-stopword characters,
    then more tokens, then earlier position. This is planning only, not a TM
    conclusion. It prevents a clean zero-result phrase from becoming structurally
    impossible to evaluate.
    """
    # Drop punctuation-created single-letter alphabetic fragments (e.g. I'M -> I/M)
    # from fallback core construction only; exact/normalized wording stays unchanged.
    toks=[t.upper() for t in _tokens(candidate_wording) if len(t)>1 or t.isdigit()]
    rows=[]
    seen=set()
    for n in (3,2):
        if len(toks)<n:
            continue
        for i in range(len(toks)-n+1):
            gram=toks[i:i+n]
            q=" ".join(gram)
            if q in seen:
                continue
            seen.add(q)
            strong_chars=sum(len(t) for t in gram if t not in STOPWORDS)
            strong_tokens=sum(1 for t in gram if t not in STOPWORDS)
            if strong_tokens==0:
                continue
            rows.append({
                "query":q,
                "token_count":n,
                "strong_token_count":strong_tokens,
                "strong_character_count":strong_chars,
                "source":"DETERMINISTIC_CLEAN_PATH_NGRAM",
                "source_rank":i+1,
            })
    if not rows and toks:
        ranked=sorted(
            [(len(t),i,t) for i,t in enumerate(toks) if t not in STOPWORDS],
            key=lambda x:(-x[0],x[1],x[2]),
        )
        for _,i,t in ranked[:limit]:
            rows.append({
                "query":t,
                "token_count":1,
                "strong_token_count":1,
                "strong_character_count":len(t),
                "source":"DETERMINISTIC_CLEAN_PATH_SINGLE_TOKEN",
                "source_rank":i+1,
            })
    rows.sort(key=lambda x:(-x["strong_character_count"],-x["strong_token_count"],-x["token_count"],x["source_rank"],x["query"]))
    return rows[:limit]


def _phonetic_token_pattern(token):
    """Return a bounded high-recall spelling/pronunciation regex fragment.

    This is intentionally conservative and not legal clearance. Vowels are
    broadened, common consonant confusions are grouped, and optional terminal e
    is allowed. Unsupported tokens still remain literal rather than disappearing.
    """
    t=re.sub(r"[^a-z]","",token.lower())
    if not t:
        return None
    groups={
        "a":"[aeiouy]","e":"[aeiouy]","i":"[aeiouy]","o":"[aeiouy]","u":"[aeiouy]","y":"[aeiouy]",
        "c":"[ckq]","k":"[ckq]","q":"[ckq]",
        "s":"[sz]","z":"[sz]",
        "g":"[gj]","j":"[gj]",
        "v":"[vw]","w":"[vw]",
    }
    out=""
    i=0
    while i<len(t):
        if t[i:i+2]=="ph":
            out+="(?:ph|f)"; i+=2; continue
        out+=groups.get(t[i],re.escape(t[i]))
        i+=1
    return out


def build_phonetic_regex_query(candidate_wording, cores):
    # Use strong tokens from the already-selected bounded cores; fall back to
    # the wording if needed. Keep at most four unique tokens to bound breadth.
    selected=[]
    for core in cores:
        for token in _tokens(core.get("query")):
            u=token.upper()
            if u in STOPWORDS or len(token)<4 or u in selected:
                continue
            selected.append(u)
    if not selected:
        for token in _tokens(candidate_wording):
            u=token.upper()
            if u in STOPWORDS or len(token)<4 or u in selected:
                continue
            selected.append(u)
    selected=selected[:4]
    patterns=[]
    for token in selected:
        frag=_phonetic_token_pattern(token)
        if frag:
            patterns.append(f"/.*{frag}.*/")
    if not patterns:
        return {"queries":[],"state":"HOLD_REQUIRED_PHONETIC_PLAN_UNAVAILABLE","tokens":[]}
    return {
        "queries":["CM:("+" AND ".join(patterns)+")"],
        "state":"REQUIRED_BOUNDED_USPTO_REGEX",
        "tokens":selected,
        "negative_semantics_required":"USPTO_NATIVE_ZERO_FOR_BOUND_REGEX",
        "legal_clearance_asserted":False,
    }


def build_query_plan(candidate_wording, priority_queue):
    normalized=normalize_wording(candidate_wording)
    surface=_surface_upper(candidate_wording)
    cores=derive_core_queries(candidate_wording,priority_queue,limit=2)
    if not cores:
        cores=derive_fallback_core_queries(candidate_wording,limit=2)
    phonetic=build_phonetic_regex_query(candidate_wording,cores)
    return {
        "required_dimensions":list(REQUIRED_DIMENSIONS),
        "EXACT":{"queries":[candidate_wording],"negative_semantics_required":"US_FEDERAL_EXACT_NEGATIVE"},
        "NORMALIZED_EXACT":{
            "queries":[normalized],
            "equivalent_to_exact_after_normalization": normalized==surface,
            "negative_semantics_required":"US_FEDERAL_NORMALIZED_EXACT_NEGATIVE",
        },
        "CORE_DOMINANT_TOKEN":{"queries":[x["query"] for x in cores],"derivation":cores},
        "EXPANDED_PARTIAL":{"queries":[x["query"] for x in cores],"derivation":"REUSE_SELECTED_CORES_WITH_PARTIAL_RECALL"},
        "PHONETIC_OR_SPELLING_WHEN_MATERIAL":phonetic,
        "RELATED_GOODS_REVIEW":{
            "state":"BOUND_RESULTSET_GOODS_REVIEW_REQUIRED",
            "negative_semantics_required":"NO_MATERIAL_RECORD_ACROSS_INTENDED_OR_COORDINATED_GOODS_FRONTIER",
        },
        "legal_clearance_asserted":False,
    }
