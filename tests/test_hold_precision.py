#!/usr/bin/env python3
from pathlib import Path

from aver.positive_recall import (
    NONMATERIAL_DEAD_UNRELATED_EXPANDED_PARTIAL_RECALL,
    UNBOUND_POSITIVE_RESULTSET,
    classify_expanded_partial_recall,
    positive_review_bucket,
)

# Unbound positive resultsets require record resolution, but are not themselves
# candidate-specific material-positive records.
assert positive_review_bucket({
    "classification": UNBOUND_POSITIVE_RESULTSET,
    "record_binding_complete": False,
}) == "UNBOUND_RESULTSET"

# A bound but unresolved record remains candidate-specific material ambiguity.
assert positive_review_bucket({
    "classification": "MATERIALITY_UNRESOLVED",
    "record_binding_complete": True,
}) == "MATERIAL_OR_UNRESOLVED"

request = {
    "intended_goods_context": {
        "primary_class": "016",
        "description": "Decorative vinyl stickers and decals",
    }
}
record = {
    "serial_number": "90347247",
    "mark_text": "ANXIETY IS MY BITCH",
    "class_codes": ["025"],
    "goods_services_excerpt": "IC 025: Shirts.",
}
dead_tsdr = "TM5 Common Status Descriptor: DEAD/ This trademark application was refused, dismissed, or invalidated by the Office and this application is no longer active."

expanded = classify_expanded_partial_recall(request, record, dead_tsdr, "EXPANDED_PARTIAL")
assert expanded["classification"] == NONMATERIAL_DEAD_UNRELATED_EXPANDED_PARTIAL_RECALL
assert expanded["record_binding_complete"] is True
assert positive_review_bucket(expanded) == "NONMATERIAL_BOUND"

# Safety floor is preserved: a core/dominant overlap is not auto-cleared merely
# because the bound record is dead and in a different class.
core = classify_expanded_partial_recall(request, record, dead_tsdr, "CORE_DOMINANT_TOKEN")
assert core["classification"] == "MATERIALITY_UNRESOLVED"
assert positive_review_bucket(core) == "MATERIAL_OR_UNRESOLVED"

# Structural regression guard: production must keep unbound resultsets separate
# from bound material-positive records and emit a distinct HOLD reason.
source = Path("src/aver/production.py").read_text(encoding="utf-8")
assert '"classification":UNBOUND_POSITIVE_RESULTSET' in source
assert "unbound_positive=[]" in source
assert '"POSITIVE_RESULTSET_RECORD_BINDING_REQUIRED"' in source
assert "all_material_positive_bound" in source
assert "material_positive_present=bool(material_positive)" in source

print("AVER_HOLD_PRECISION_TEST_PASS")
