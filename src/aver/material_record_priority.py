#!/usr/bin/env python3
import re
from urllib.parse import urlparse


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


def _mark_from_record_url(url, serial):
    path=urlparse(url or "").path.rstrip("/").split("/")[-1]
    suffix="-"+str(serial)
    if path.endswith(suffix):
        path=path[:-len(suffix)]
    return " ".join(x for x in path.replace("_","-").split("-") if x).upper()


def _classes(anchor):
    values=[]
    for value in re.findall(r"\bClass\s+(\d{3})\b", anchor.get("anchor_text") or "", re.I):
        if value not in values:
            values.append(value)
    return values


def prioritize_material_records(candidate_wording, anchors, primary_class="016", merch_adjacent_classes=("025",), limit=8):
    """Rank discovered record anchors for deep review; never decide safety.

    Score is only work-order triage. Exact primary-class and merch-adjacent-class
    evidence increases inspection priority but cannot produce TM_KILL/TM_PASS.
    """
    c=_tokens(candidate_wording)
    output=[]
    for anchor in anchors:
        serial=str(anchor.get("identifier") or "")
        mark=_mark_from_record_url(anchor.get("record_url"), serial)
        m=_tokens(mark)
        shared=set(c)&set(m)
        contiguous=_longest_contiguous_shared(c,m)
        classes=_classes(anchor)
        full_mark_contained=bool(m) and any(c[i:i+len(m)]==m for i in range(max(0,len(c)-len(m)+1)))
        candidate_contained=bool(c) and any(m[i:i+len(c)]==c for i in range(max(0,len(m)-len(c)+1)))
        score=0
        factors=[]
        if c==m and c:
            score+=100; factors.append("EXACT_WORDING")
        elif full_mark_contained or candidate_contained:
            score+=60; factors.append("FULL_MARK_CONTAINMENT")
        if contiguous:
            score+=12*len(contiguous); factors.append(f"CONTIGUOUS_SHARED_{len(contiguous)}")
        if shared:
            score+=4*len(shared); factors.append(f"SHARED_TOKENS_{len(shared)}")
        if primary_class in classes:
            score+=35; factors.append("PRIMARY_CLASS_MATCH")
        adjacent=[x for x in classes if x in merch_adjacent_classes]
        if adjacent:
            score+=15; factors.append("MERCH_ADJACENT_CLASS_PRESENT")
        output.append({
            "identifier":serial,
            "record_url":anchor.get("record_url"),
            "mark_text":mark,
            "classes":classes,
            "priority_score":score,
            "priority_factors":factors,
            "shared_tokens":sorted(shared),
            "longest_shared_contiguous_tokens":contiguous,
            "full_mark_contained":full_mark_contained,
            "candidate_contained":candidate_contained,
            "safety_decision":None,
            "legal_clearance_asserted":False,
        })
    output.sort(key=lambda x:(-x["priority_score"],x["identifier"]))
    return output[:limit]
