#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

from jsonschema import validate

import sys
sys.path.insert(0, str(Path("src/aver").resolve()))
from decision import evaluate_tm_state

request_schema = json.loads(Path("spec/request.schema.json").read_text())
receipt_schema = json.loads(Path("spec/receipt.schema.json").read_text())


def base_state():
    return {
        "material_positive_record_present": False,
        "record_binding_complete": True,
        "similarity_assessment": "CLEAR",
        "goods_relatedness_assessment": "CLEAR",
        "required_query_dimensions_complete": True,
        "resolver_scope_complete": True,
        "unresolved_dimensions": [],
        "negative_evidence_distinct_sources": 2,
        "scope_qualified_negative_evidence_distinct_sources": 2,
        "transport_blocked": False,
        "control_blocked": False,
        "source_discordance": False,
    }


def assert_decision(name, overrides, expected):
    state = base_state()
    state.update(overrides)
    result = evaluate_tm_state(state)
    assert result["decision"] == expected, (name, result)
    assert result["legal_clearance_asserted"] is False, name
    assert result["decision_reason_codes"], name
    return result


assert_decision(
    "material-positive-kill",
    {
        "material_positive_record_present": True,
        "record_binding_complete": True,
        "similarity_assessment": "MATERIAL",
        "goods_relatedness_assessment": "MATERIAL",
        "negative_evidence_distinct_sources": 4,
        "scope_qualified_negative_evidence_distinct_sources": 4,
    },
    "TM_KILL",
)
assert_decision("positive-record-binding-incomplete", {"material_positive_record_present": True, "record_binding_complete": False}, "TM_HOLD")
assert_decision("positive-similarity-unresolved", {"material_positive_record_present": True, "similarity_assessment": "UNRESOLVED", "goods_relatedness_assessment": "MATERIAL"}, "TM_HOLD")
assert_decision("transport-block", {"transport_blocked": True}, "TM_HOLD")
assert_decision("control-block", {"control_blocked": True}, "TM_HOLD")
assert_decision("missing-query-dimension", {"required_query_dimensions_complete": False}, "TM_HOLD")
assert_decision("scope-incomplete", {"resolver_scope_complete": False}, "TM_HOLD")
assert_decision("explicit-unresolved-dimension", {"unresolved_dimensions": ["PHONETIC_OR_SPELLING_WHEN_MATERIAL"]}, "TM_HOLD")
assert_decision("single-negative-source", {"negative_evidence_distinct_sources": 1, "scope_qualified_negative_evidence_distinct_sources": 1}, "TM_HOLD")
assert_decision("source-discordance", {"source_discordance": True}, "TM_HOLD")
assert_decision("similarity-unresolved", {"similarity_assessment": "UNRESOLVED"}, "TM_HOLD")
assert_decision("goods-unresolved", {"goods_relatedness_assessment": "UNRESOLVED"}, "TM_HOLD")

# Raw source count must never substitute for scope-qualified convergence.
assert_decision(
    "class016-trademarkia-plus-tmhunt-not-enough",
    {"negative_evidence_distinct_sources": 2, "scope_qualified_negative_evidence_distinct_sources": 1},
    "TM_HOLD",
)

pass_result = assert_decision("complete-convergent-negative", {}, "TM_PASS")
assert pass_result["confidence_label"] == "FALLBACK_HIGH_CONFIDENCE"

request = {
    "schema": "AVER_TM_REQUEST",
    "schema_version": "1.0",
    "request_id": "daily7:2026-09-12:test-01",
    "wording": "Example phrase",
    "intended_goods_context": {
        "primary_class": "016",
        "coordinated_classes": ["025"],
        "description": "Printed stickers for laptops and water bottles",
        "channels": ["Amazon US"],
        "purchasers": ["US retail consumers"]
    },
    "requested_scope": {
        "country": "US",
        "federal_registry": True,
        "related_goods_review": True,
        "query_dimensions": ["EXACT", "NORMALIZED_EXACT", "CORE_DOMINANT_TOKEN", "EXPANDED_PARTIAL", "PHONETIC_OR_SPELLING_WHEN_MATERIAL", "RELATED_GOODS_REVIEW"]
    },
    "caller": {"system": "Daily7", "reference": "shadow-only"}
}
validate(request, request_schema)
request_hash = hashlib.sha256(json.dumps(request, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

receipt = {
    "schema": "AVER_TM_RECEIPT",
    "schema_version": "1.0",
    "engine_version": "0.1.0",
    "engine_commit_sha": "a" * 40,
    "request_id": request["request_id"],
    "request_sha256": request_hash,
    "decision": pass_result["decision"],
    "confidence_label": pass_result["confidence_label"],
    "legal_clearance_asserted": False,
    "decision_reason_codes": pass_result["decision_reason_codes"],
    "query_plan": [{"dimension": d, "state": "RESOLVED", "resolver": "DECLARED_PROFILE"} for d in request["requested_scope"]["query_dimensions"]],
    "resolver_evidence": [
        {"resolver": "FEDERAL_SCOPE_SOURCE_A", "scope": "US_FEDERAL_CLASS016_RELEVANT", "state": "RESULTSET_RESOLVED", "evidence_polarity": "NEGATIVE", "evidence_hash": "b" * 64},
        {"resolver": "FEDERAL_SCOPE_SOURCE_B", "scope": "US_FEDERAL_CLASS016_RELEVANT", "state": "RESULTSET_RESOLVED", "evidence_polarity": "NEGATIVE", "evidence_hash": "c" * 64}
    ],
    "material_records": [],
    "unresolved_dimensions": [],
    "scope_coverage": {
        "required_query_dimensions_complete": True,
        "resolver_scope_complete": True,
        "negative_evidence_distinct_sources": 2,
        "scope_qualified_negative_evidence_distinct_sources": 2
    },
    "similarity_analysis": "CLEAR",
    "goods_relatedness": "CLEAR",
    "evidence_hashes": ["b" * 64, "c" * 64]
}
validate(receipt, receipt_schema)
assert "safe" not in receipt
assert receipt["legal_clearance_asserted"] is False

forbidden_request = dict(request)
forbidden_request["engine_authority"] = "caller"
try:
    validate(forbidden_request, request_schema)
    raise AssertionError("request schema accepted caller authority")
except Exception:
    pass

forbidden_receipt = dict(receipt)
forbidden_receipt["safe"] = True
try:
    validate(forbidden_receipt, receipt_schema)
    raise AssertionError("receipt schema accepted generic safe boolean")
except Exception:
    pass

print("AVER_CONTRACT_MATRIX_PASS")
