#!/usr/bin/env python3

REQUIRED_DIMENSIONS = [
    "EXACT",
    "NORMALIZED_EXACT",
    "CORE_DOMINANT_TOKEN",
    "EXPANDED_PARTIAL",
    "PHONETIC_OR_SPELLING_WHEN_MATERIAL",
    "RELATED_GOODS_REVIEW",
]

TERMINAL_STATES = {
    "RESOLVED_NEGATIVE",
    "RESOLVED_POSITIVE",
    "HOLD_CAPABILITY",
    "HOLD_EVIDENCE",
    "SKIPPED_AFTER_MATERIAL_CONFLICT",
}


def resolve_dimension(*, dimension, execution_state, evidence_polarity=None,
                      negative_semantics_scope_ok=False,
                      positive_record_bound=False,
                      material_conflict_already_proven=False,
                      material_trigger=True):
    """Map one required query dimension to a fail-closed terminal semantic.

    This function never emits a TM decision. It only states whether the required
    dimension is resolved, positively escalated, or blocked by capability/evidence.
    """
    if dimension not in REQUIRED_DIMENSIONS:
        raise ValueError(f"UNKNOWN_REQUIRED_DIMENSION:{dimension}")

    if material_conflict_already_proven:
        return {
            "dimension": dimension,
            "terminal_state": "SKIPPED_AFTER_MATERIAL_CONFLICT",
            "scope_complete_for_negative_pass": False,
            "reason": "EARLY_STOP_AFTER_PROVEN_MATERIAL_CONFLICT",
        }

    if dimension == "PHONETIC_OR_SPELLING_WHEN_MATERIAL" and material_trigger is False:
        return {
            "dimension": dimension,
            "terminal_state": "RESOLVED_NEGATIVE",
            "scope_complete_for_negative_pass": True,
            "reason": "MACHINE_PROVEN_NOT_MATERIAL_FOR_THIS_CANDIDATE",
        }

    if execution_state in {"CAPABILITY_UNAVAILABLE", "CONTROL_BLOCKED", "TRANSPORT_BLOCKED"}:
        return {
            "dimension": dimension,
            "terminal_state": "HOLD_CAPABILITY",
            "scope_complete_for_negative_pass": False,
            "reason": "REQUIRED_DIMENSION_CAPABILITY_NOT_AVAILABLE",
        }

    if execution_state != "EXECUTED":
        return {
            "dimension": dimension,
            "terminal_state": "HOLD_EVIDENCE",
            "scope_complete_for_negative_pass": False,
            "reason": "REQUIRED_DIMENSION_NOT_MACHINE_EXECUTED",
        }

    if evidence_polarity == "POSITIVE":
        if positive_record_bound:
            return {
                "dimension": dimension,
                "terminal_state": "RESOLVED_POSITIVE",
                "scope_complete_for_negative_pass": False,
                "reason": "POSITIVE_RECORD_BOUND_FOR_MATERIAL_REVIEW",
            }
        return {
            "dimension": dimension,
            "terminal_state": "HOLD_EVIDENCE",
            "scope_complete_for_negative_pass": False,
            "reason": "POSITIVE_RESULTSET_WITHOUT_RECORD_BINDING",
        }

    if evidence_polarity == "NEGATIVE":
        if negative_semantics_scope_ok:
            return {
                "dimension": dimension,
                "terminal_state": "RESOLVED_NEGATIVE",
                "scope_complete_for_negative_pass": True,
                "reason": "NEGATIVE_SEMANTICS_MACHINE_PROVEN_FOR_REQUIRED_SCOPE",
            }
        return {
            "dimension": dimension,
            "terminal_state": "HOLD_EVIDENCE",
            "scope_complete_for_negative_pass": False,
            "reason": "NEGATIVE_RESULT_WITHOUT_REQUIRED_SCOPE_SEMANTICS",
        }

    return {
        "dimension": dimension,
        "terminal_state": "HOLD_EVIDENCE",
        "scope_complete_for_negative_pass": False,
        "reason": "RESULTSET_POLARITY_OR_MEANING_UNRESOLVED",
    }


def evaluate_required_scope(dimension_records):
    by_dimension = {r["dimension"]: r for r in dimension_records}
    missing = [d for d in REQUIRED_DIMENSIONS if d not in by_dimension]
    invalid = [
        d for d, r in by_dimension.items()
        if r.get("terminal_state") not in TERMINAL_STATES
    ]
    unresolved = [
        d for d in REQUIRED_DIMENSIONS
        if d in by_dimension and by_dimension[d]["terminal_state"] in {"HOLD_CAPABILITY", "HOLD_EVIDENCE"}
    ]
    positive = [
        d for d in REQUIRED_DIMENSIONS
        if d in by_dimension and by_dimension[d]["terminal_state"] == "RESOLVED_POSITIVE"
    ]
    skipped_after_conflict = [
        d for d in REQUIRED_DIMENSIONS
        if d in by_dimension and by_dimension[d]["terminal_state"] == "SKIPPED_AFTER_MATERIAL_CONFLICT"
    ]
    negative_scope_complete = bool(
        not missing and not invalid and not unresolved and not positive and not skipped_after_conflict
        and all(by_dimension[d].get("scope_complete_for_negative_pass") is True for d in REQUIRED_DIMENSIONS)
    )
    return {
        "required_dimensions": list(REQUIRED_DIMENSIONS),
        "missing_dimensions": missing,
        "invalid_dimensions": invalid,
        "unresolved_dimensions": unresolved,
        "positive_dimensions": positive,
        "skipped_after_material_conflict": skipped_after_conflict,
        "negative_scope_complete": negative_scope_complete,
        "semantics_complete": not missing and not invalid,
    }
