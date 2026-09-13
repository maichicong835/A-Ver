#!/usr/bin/env python3
import re


def _tokens(value):
    return re.findall(r"[a-z0-9]+", (value or "").lower())


def _longest_contiguous_shared(a, b):
    best=[]
    for i in range(len(a)):
        for j in range(len(b)):
            k=0
            while i+k < len(a) and j+k < len(b) and a[i+k]==b[j+k]:
                k+=1
            if k > len(best):
                best=a[i:i+k]
    return best


def analyze_word_mark_similarity(candidate_wording, record_mark, component_strength_state="UNRESOLVED"):
    """Produce bounded word-mark similarity evidence without legal conclusion.

    A shared component cannot by itself become MATERIAL when its strength is
    unresolved and both marks contain substantial different remainder wording.
    Conversely this function never returns CLEAR solely from different tails.
    """
    c=_tokens(candidate_wording)
    r=_tokens(record_mark)
    shared=set(c) & set(r)
    contiguous=_longest_contiguous_shared(c,r)
    candidate_only=[x for x in c if x not in shared]
    record_only=[x for x in r if x not in shared]
    exact=(c==r and bool(c))
    record_contained=bool(r) and any(c[i:i+len(r)]==r for i in range(max(0,len(c)-len(r)+1)))
    candidate_contained=bool(c) and any(r[i:i+len(c)]==c for i in range(max(0,len(r)-len(c)+1)))

    if exact or record_contained or candidate_contained:
        assessment="MATERIAL"
        reasons=["EXACT_OR_FULL_MARK_CONTAINMENT"]
    elif len(contiguous) >= 2 and candidate_only and record_only:
        if component_strength_state == "STRONG_OR_DISTINCTIVE":
            assessment="MATERIAL"
            reasons=["SHARED_CONTIGUOUS_COMPONENT", "SHARED_COMPONENT_MACHINE_PROVEN_STRONG"]
        else:
            assessment="UNRESOLVED"
            reasons=["SHARED_CONTIGUOUS_COMPONENT", "DISTINCT_REMAINDERS_PRESENT", "SHARED_COMPONENT_STRENGTH_UNRESOLVED"]
    elif not shared:
        assessment="UNRESOLVED"
        reasons=["NO_SHARED_WORD_TOKENS", "PHONETIC_SEMANTIC_APPEARANCE_REVIEW_NOT_COMPLETED"]
    else:
        assessment="UNRESOLVED"
        reasons=["LIMITED_WORD_OVERLAP", "PHONETIC_SEMANTIC_APPEARANCE_REVIEW_NOT_COMPLETED"]

    return {
        "assessment": assessment,
        "reason_codes": reasons,
        "candidate_tokens": c,
        "record_tokens": r,
        "shared_tokens": sorted(shared),
        "longest_shared_contiguous_tokens": contiguous,
        "candidate_only_tokens": candidate_only,
        "record_only_tokens": record_only,
        "exact": exact,
        "record_mark_fully_contained": record_contained,
        "candidate_fully_contained": candidate_contained,
        "component_strength_state": component_strength_state,
        "phonetic_review_complete": False,
        "semantic_review_complete": False,
        "appearance_review_complete": False,
        "commercial_impression_complete": False,
        "legal_clearance_asserted": False,
    }
