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

    Exact wording may be material on its face. Full containment of a multi-token
    mark may also be material. But a single-token mark contained inside a longer
    phrase must not become MATERIAL unless the shared component has separately
    been machine-proven strong/distinctive. This prevents common, descriptive,
    or semantically different single words from creating an automatic conflict.
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
    containment=record_contained or candidate_contained
    contained_token_count=min(len(c),len(r)) if containment else 0
    single_token_containment=bool(containment and not exact and contained_token_count==1)

    if exact:
        assessment="MATERIAL"
        reasons=["EXACT_WORDING"]
    elif single_token_containment:
        if component_strength_state == "STRONG_OR_DISTINCTIVE":
            assessment="MATERIAL"
            reasons=["SINGLE_TOKEN_CONTAINMENT", "SHARED_COMPONENT_MACHINE_PROVEN_STRONG"]
        else:
            assessment="UNRESOLVED"
            reasons=["SINGLE_TOKEN_CONTAINMENT", "SHARED_COMPONENT_STRENGTH_UNRESOLVED", "SEMANTIC_AND_COMMERCIAL_IMPRESSION_REVIEW_REQUIRED"]
    elif containment:
        assessment="MATERIAL"
        reasons=["MULTI_TOKEN_FULL_MARK_CONTAINMENT"]
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
        "single_token_containment": single_token_containment,
        "component_strength_state": component_strength_state,
        "phonetic_review_complete": False,
        "semantic_review_complete": False,
        "appearance_review_complete": False,
        "commercial_impression_complete": False,
        "legal_clearance_asserted": False,
    }
