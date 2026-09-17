#!/usr/bin/env python3
import re

STICKER_GOODS_ANCHORS={"sticker","stickers","decal","decals"}
UNBOUND_POSITIVE_RESULTSET="UNBOUND_POSITIVE_RESULTSET"
NONMATERIAL_DEAD_UNRELATED_EXPANDED_PARTIAL_RECALL="NONMATERIAL_DEAD_UNRELATED_EXPANDED_PARTIAL_RECALL"


def _tokens(value): return set(re.findall(r"[a-z0-9]+",(value or "").lower()))


def classify_tsdr_current_status(body):
 text=re.sub(r"\s+"," ",body or "").strip().lower()
 dead=("tm5 common status descriptor: dead/","this trademark application was refused, dismissed, or invalidated by the office and this application is no longer active","this trademark registration was cancelled or expired and is no longer active","status: application is void","status: abandoned","status: cancelled","status: canceled","status: expired")
 active=("tm5 common status descriptor: live/","this trademark application is currently active","this trademark registration is currently active")
 d=any(x in text for x in dead); a=any(x in text for x in active)
 if d and a: return {"state":"UNRESOLVED","machine_bound":False,"reason":"CONTRADICTORY_TSDR_CURRENT_STATUS_MARKERS"}
 if d: return {"state":"DEAD_INACTIVE","machine_bound":True,"reason":"EXPLICIT_TSDR_CURRENT_STATUS_DEAD_OR_INACTIVE"}
 if a: return {"state":"LIVE_ACTIVE","machine_bound":True,"reason":"EXPLICIT_TSDR_CURRENT_STATUS_LIVE_OR_ACTIVE"}
 return {"state":"UNRESOLVED","machine_bound":False,"reason":"TSDR_CURRENT_STATUS_NOT_UNAMBIGUOUSLY_BOUND"}


def classify_expanded_partial_recall(request,record_detail,tsdr_body,dimension):
 status=classify_tsdr_current_status(tsdr_body); classes={str(x).zfill(3) for x in (record_detail or {}).get("class_codes") or []}; goods_tokens=_tokens((record_detail or {}).get("goods_services_excerpt") or "")
 intended=(request or {}).get("intended_goods_context") or {}; primary=str(intended.get("primary_class") or "").zfill(3); intended_tokens=_tokens(intended.get("description") or "")
 sticker_intent=bool(STICKER_GOODS_ANCHORS & intended_tokens) or "adhesive" in intended_tokens; explicit_sticker_goods=bool(STICKER_GOODS_ANCHORS & goods_tokens); class_overlap=bool(primary and primary in classes); bound=bool((record_detail or {}).get("serial_number") and (record_detail or {}).get("mark_text"))
 nonmaterial=bool(dimension=="EXPANDED_PARTIAL" and bound and status["state"]=="DEAD_INACTIVE" and primary=="016" and sticker_intent and not class_overlap and not explicit_sticker_goods)
 return {"classification":NONMATERIAL_DEAD_UNRELATED_EXPANDED_PARTIAL_RECALL if nonmaterial else "MATERIALITY_UNRESOLVED","record_binding_complete":bound and status["machine_bound"],"tsdr_status":status,"dimension":dimension,"primary_class":primary,"record_classes":sorted(classes),"class_overlap":class_overlap,"sticker_intent":sticker_intent,"explicit_sticker_goods":explicit_sticker_goods,"federal_scope_only":True,"common_law_clearance_asserted":False,"legal_clearance_asserted":False}


def positive_review_bucket(review):
 """Separate candidate-specific materiality from unresolved resultset binding.

 A positive resultset without a bound federal record is evidence that more
 record resolution is needed; it is not itself a material-positive record.
 This helper does not grant TM_PASS or legal clearance. It only prevents an
 unbound broad resultset from being mislabelled as a candidate-specific
 material conflict.
 """
 review=review or {}
 classification=review.get("classification")
 bound=bool(review.get("record_binding_complete"))
 if classification==NONMATERIAL_DEAD_UNRELATED_EXPANDED_PARTIAL_RECALL and bound:
  return "NONMATERIAL_BOUND"
 if classification==UNBOUND_POSITIVE_RESULTSET:
  return "UNBOUND_RESULTSET"
 return "MATERIAL_OR_UNRESOLVED"
