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
    """Derive bounded core queries from machine-observed material-record overlap.

    This avoids inventing a subjective 'dominant word' before evidence exists.
    Multi-token shared components outrank single-token components; priority order
    breaks ties. The output is work-order data, never a safety conclusion.
    """
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
            "source_record_identifier":item.get("identifier"),
            "source_record_priority":item.get("priority_score",0),
            "source_rank":rank+1,
        })
    candidates.sort(key=lambda x:(-x["token_count"],-x["source_record_priority"],x["source_rank"],x["query"]))
    return candidates[:limit]


def build_query_plan(candidate_wording, priority_queue):
    normalized=normalize_wording(candidate_wording)
    surface=_surface_upper(candidate_wording)
    cores=derive_core_queries(candidate_wording,priority_queue,limit=2)
    return {
        "required_dimensions":list(REQUIRED_DIMENSIONS),
        "EXACT":{"queries":[candidate_wording],"negative_semantics_required":"US_FEDERAL_EXACT_NEGATIVE"},
        "NORMALIZED_EXACT":{
            "queries":[normalized],
            "equivalent_to_exact_after_normalization": normalized==surface,
            "negative_semantics_required":"US_FEDERAL_NORMALIZED_EXACT_NEGATIVE",
        },
        "CORE_DOMINANT_TOKEN":{"queries":[x["query"] for x in cores],"derivation":cores},
        "EXPANDED_PARTIAL":{"queries":[x["query"] for x in cores],"derivation":"REUSE_EVIDENCE_DERIVED_CORES_WITH_PARTIAL_RECALL"},
        "PHONETIC_OR_SPELLING_WHEN_MATERIAL":{"queries":[],"state":"UNRESOLVED_POLICY_NOT_MACHINE_PROVEN"},
        "RELATED_GOODS_REVIEW":{"state":"DEFER_TO_BOUND_MATERIAL_FRONTIER"},
        "legal_clearance_asserted":False,
    }
