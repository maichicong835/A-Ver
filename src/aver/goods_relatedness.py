#!/usr/bin/env python3
import re


def _tokens(value):
    return [x for x in re.findall(r"[a-z0-9]+", (value or "").lower()) if x]


def evaluate_g0_g4(intended, bound_record):
    """Conservative G0-G4 evidence map for a single bound trademark record.

    Only G0/G1 are machine-resolved from the bound federal record here.
    G2-G4 remain unresolved unless explicit evidence is supplied by later layers.
    This function does not decide likelihood of confusion or TM outcome.
    """
    intended_class = str(intended.get("primary_class") or "").zfill(3)
    intended_goods = (intended.get("description") or "").strip()
    intended_goods_tokens = set(_tokens(intended_goods))

    record_classes = set(bound_record.get("class_codes") or [])
    class_details = bound_record.get("class_details") or []
    record_goods_text = " ".join(x.get("goods_services_text") or "" for x in class_details)
    record_goods_tokens = set(_tokens(record_goods_text))

    g0_class_overlap = bool(intended_class and intended_class in record_classes)

    # High-signal exact/near-exact goods anchors for sticker use. The caller's
    # description remains data; this evaluator does not infer unrelated goods.
    sticker_intent = any(t in intended_goods_tokens for t in ("sticker", "stickers", "adhesive"))
    sticker_record = any(t in record_goods_tokens for t in ("sticker", "stickers"))
    g1_explicit_goods_overlap = bool(sticker_intent and sticker_record)

    axes = {
        "G0_CLASS_OVERLAP": {
            "state": "RESOLVED",
            "material": g0_class_overlap,
            "intended_class": intended_class,
            "record_classes": sorted(record_classes),
        },
        "G1_EXPLICIT_GOODS_OVERLAP": {
            "state": "RESOLVED",
            "material": g1_explicit_goods_overlap,
            "intended_goods": intended_goods,
            "record_goods_excerpt": record_goods_text[:2500],
            "sticker_intent": sticker_intent,
            "sticker_record": sticker_record,
        },
        "G2_COORDINATED_OR_ADJACENT_CLASSES": {
            "state": "UNRESOLVED",
            "material": None,
            "reason": "NO_MACHINE_PROVEN_COORDINATED_CLASS_EVIDENCE_IN_THIS_LAYER",
        },
        "G3_CHANNELS_AND_PURCHASERS": {
            "state": "UNRESOLVED",
            "material": None,
            "reason": "NO_BOUND_CHANNEL_OR_PURCHASER_EVIDENCE_IN_FEDERAL_RECORD_DETAIL",
        },
        "G4_REGISTRANT_MARKETPLACE_OR_MERCH_PRESENCE": {
            "state": "UNRESOLVED",
            "material": None,
            "reason": "MARKETPLACE_CORROBORATION_NOT_EXECUTED_IN_THIS_LAYER",
        },
    }

    if g1_explicit_goods_overlap:
        assessment = "MATERIAL"
        reason_codes = ["EXPLICIT_STICKER_GOODS_OVERLAP"]
        if g0_class_overlap:
            reason_codes.append("PRIMARY_CLASS_OVERLAP")
    else:
        assessment = "UNRESOLVED"
        reason_codes = ["NO_EXPLICIT_STICKER_GOODS_OVERLAP_ON_BOUND_RECORD", "G2_G4_STILL_UNRESOLVED"]

    return {
        "assessment": assessment,
        "reason_codes": reason_codes,
        "axes": axes,
        "g0_g1_resolved": True,
        "g2_g4_resolved": False,
        "legal_clearance_asserted": False,
    }
