#!/usr/bin/env python3
import re

STICKER_GOODS_ANCHORS={"sticker","stickers","decal","decals"}


def _tokens(value):
    return set(re.findall(r"[a-z0-9]+",(value or "").lower()))


def classify_tsdr_current_status(body):
    """Conservatively classify current TSDR status text.

    Historical words such as REGISTERED elsewhere on the page are ignored. A
    dead/inactive result requires an explicit current-status phrase from TSDR.
    """
    text=re.sub(r"\s+"," ",body or "").strip()
    low=text.lower()
    dead_markers=(
        "tm5 common status descriptor: dead/",
        "this trademark application was refused, dismissed, or invalidated by the office and this application is no longer active",
        "this trademark registration was cancelled or expired and is no longer active",
        "status: application is void",
        "status: abandoned",
        "status: cancelled",
        "status: canceled",
        "status: expired",
    )
    if any(x in low for x in dead_markers):
        return {
            "state":"DEAD_INACTIVE",
            "machine_bound":True,
            "reason":"EXPLICIT_TSDR_CURRENT_STATUS_DEAD_OR_INACTIVE",
        }
    active_markers=(
        "tm5 common status descriptor: live/",
        "this trademark application is currently active",
        "this trademark registration is currently active",
    )
    if any(x in low for x in active_markers):
        return {
            "state":"LIVE_ACTIVE",
            "machine_bound":True,
            "reason":"EXPLICIT_TSDR_CURRENT_STATUS_LIVE_OR_ACTIVE",
        }
    return {
        "state":"UNRESOLVED",
        "machine_bound":False,
        "reason":"TSDR_CURRENT_STATUS_NOT_UNAMBIGUOUSLY_BOUND",
    }


def classify_expanded_partial_recall(request,record_detail,tsdr_body,dimension):
    """Classify only a narrow dead/unrelated expanded-partial federal recall.

    This never clears exact, normalized-exact, core-exact, or phonetic hits.
    It also does not assert common-law safety or legal clearance.
    """
    status=classify_tsdr_current_status(tsdr_body)
    classes={str(x).zfill(3) for x in (record_detail or {}).get("class_codes") or []}
    goods=(record_detail or {}).get("goods_services_excerpt") or ""
    goods_tokens=_tokens(goods)
    intended=(request or {}).get("intended_goods_context") or {}
    primary=str(intended.get("primary_class") or "").zfill(3)
    intended_tokens=_tokens(intended.get("description") or "")
    sticker_intent=bool(STICKER_GOODS_ANCHORS & intended_tokens) or "adhesive" in intended_tokens
    explicit_sticker_goods=bool(STICKER_GOODS_ANCHORS & goods_tokens)
    class_overlap=bool(primary and primary in classes)
    bound_record=bool((record_detail or {}).get("serial_number") and (record_detail or {}).get("mark_text"))

    narrow_nonmaterial=bool(
        dimension=="EXPANDED_PARTIAL"
        and bound_record
        and status["state"]=="DEAD_INACTIVE"
        and primary=="016"
        and sticker_intent
        and not class_overlap
        and not explicit_sticker_goods
    )
    return {
        "classification":"NONMATERIAL_DEAD_UNRELATED_EXPANDED_PARTIAL_RECALL" if narrow_nonmaterial else "MATERIALITY_UNRESOLVED",
        "record_binding_complete":bound_record and status["machine_bound"],
        "tsdr_status":status,
        "dimension":dimension,
        "primary_class":primary,
        "record_classes":sorted(classes),
        "class_overlap":class_overlap,
        "sticker_intent":sticker_intent,
        "explicit_sticker_goods":explicit_sticker_goods,
        "federal_scope_only":True,
        "common_law_clearance_asserted":False,
        "legal_clearance_asserted":False,
    }
