#!/usr/bin/env python3
from aver.positive_recall import classify_expanded_partial_recall, classify_tsdr_current_status

REQ={
    "intended_goods_context":{
        "primary_class":"016",
        "description":"decorative adhesive stickers",
    }
}
RECORD={
    "serial_number":"77348348",
    "mark_text":"COMPUTER SOFTWARE APPLICATION/TOOL BASED ON MS EXCEL (SPREADSHEET)",
    "class_codes":["009"],
    "goods_services_excerpt":"IC 009: Computer software development tools; computer software for organizing digital images.",
}
DEAD_BODY=(
    "TM5 Common Status Descriptor: DEAD/APPLICATION/Refused/Dismissed or Invalidated "
    "This trademark application was refused, dismissed, or invalidated by the Office and this application is no longer active. "
    "Status: Application is void because it did not meet minimum filing date requirements."
)

s=classify_tsdr_current_status(DEAD_BODY)
assert s["state"]=="DEAD_INACTIVE" and s["machine_bound"] is True, s

r=classify_expanded_partial_recall(REQ,RECORD,DEAD_BODY,"EXPANDED_PARTIAL")
assert r["classification"]=="NONMATERIAL_DEAD_UNRELATED_EXPANDED_PARTIAL_RECALL", r
assert r["record_binding_complete"] is True, r
assert r["legal_clearance_asserted"] is False and r["common_law_clearance_asserted"] is False

# The same dead record must NOT be auto-dismissed if it appears at a stronger query dimension.
for dimension in ("EXACT","NORMALIZED_EXACT","CORE_DOMINANT_TOKEN","PHONETIC_OR_SPELLING_WHEN_MATERIAL"):
    x=classify_expanded_partial_recall(REQ,RECORD,DEAD_BODY,dimension)
    assert x["classification"]=="MATERIALITY_UNRESOLVED", (dimension,x)

# A live record, Class 016 overlap, or explicit sticker goods must never take the narrow nonmaterial path.
live=DEAD_BODY.replace("DEAD/APPLICATION/Refused/Dismissed or Invalidated","LIVE/APPLICATION/Under Examination").replace("is no longer active","is currently active").replace("Status: Application is void because it did not meet minimum filing date requirements.","")
x=classify_expanded_partial_recall(REQ,RECORD,live,"EXPANDED_PARTIAL")
assert x["classification"]=="MATERIALITY_UNRESOLVED", x

class16={**RECORD,"class_codes":["016"]}
x=classify_expanded_partial_recall(REQ,class16,DEAD_BODY,"EXPANDED_PARTIAL")
assert x["classification"]=="MATERIALITY_UNRESOLVED", x

stickers={**RECORD,"goods_services_excerpt":"IC 009: downloadable software; IC 016: printed stickers and decals"}
x=classify_expanded_partial_recall(REQ,stickers,DEAD_BODY,"EXPANDED_PARTIAL")
assert x["classification"]=="MATERIALITY_UNRESOLVED", x

print("AVER_POSITIVE_RECALL_TRIAGE_CONTRACT_PASS")
