#!/usr/bin/env python3


def evaluate_tm_state(state):
    """Map normalized trademark evidence into an operational TM state.

    This is not legal clearance. A-Ver uses conservative asymmetry:
    material positive evidence can stop immediately, while negative PASS requires
    complete required scope plus convergent negative evidence.
    """
    material_positive = bool(state.get("material_positive_record_present"))
    record_binding_complete = bool(state.get("record_binding_complete"))
    similarity = state.get("similarity_assessment", "UNRESOLVED")
    goods = state.get("goods_relatedness_assessment", "UNRESOLVED")
    required_complete = bool(state.get("required_query_dimensions_complete"))
    resolver_scope_complete = bool(state.get("resolver_scope_complete"))
    unresolved = list(state.get("unresolved_dimensions") or [])
    negative_sources = int(state.get("negative_evidence_distinct_sources") or 0)
    transport_blocked = bool(state.get("transport_blocked"))
    control_blocked = bool(state.get("control_blocked"))
    source_discordance = bool(state.get("source_discordance"))

    def result(decision, confidence, reasons):
        return {
            "decision": decision,
            "confidence_label": confidence,
            "legal_clearance_asserted": False,
            "decision_reason_codes": reasons,
        }

    if material_positive:
        if not record_binding_complete:
            return result("TM_HOLD", "EVIDENCE_INCOMPLETE", ["MATERIAL_POSITIVE_RECORD_BINDING_INCOMPLETE"])
        if similarity == "MATERIAL" and goods == "MATERIAL":
            return result("TM_KILL", "POSITIVE_CONFLICT_HIGH_CONFIDENCE", ["MATERIAL_POSITIVE_RECORD", "MATERIAL_SIMILARITY", "MATERIAL_GOODS_RELATEDNESS"])
        if similarity == "UNRESOLVED" or goods == "UNRESOLVED":
            return result("TM_HOLD", "EVIDENCE_INCOMPLETE", ["MATERIAL_POSITIVE_REQUIRES_SIMILARITY_AND_GOODS_RESOLUTION"])

    if control_blocked:
        return result("TM_HOLD", "EVIDENCE_INCOMPLETE", ["CONTROL_BLOCKED"])
    if transport_blocked:
        return result("TM_HOLD", "EVIDENCE_INCOMPLETE", ["TRANSPORT_BLOCKED"])
    if unresolved:
        return result("TM_HOLD", "EVIDENCE_INCOMPLETE", ["UNRESOLVED_REQUIRED_DIMENSIONS"])
    if not required_complete:
        return result("TM_HOLD", "EVIDENCE_INCOMPLETE", ["REQUIRED_QUERY_DIMENSIONS_INCOMPLETE"])
    if not resolver_scope_complete:
        return result("TM_HOLD", "EVIDENCE_INCOMPLETE", ["RESOLVER_SCOPE_INCOMPLETE"])
    if source_discordance:
        return result("TM_HOLD", "EVIDENCE_INCOMPLETE", ["SOURCE_DISCORDANCE"])
    if similarity == "UNRESOLVED":
        return result("TM_HOLD", "EVIDENCE_INCOMPLETE", ["SIMILARITY_UNRESOLVED"])
    if goods == "UNRESOLVED":
        return result("TM_HOLD", "EVIDENCE_INCOMPLETE", ["GOODS_RELATEDNESS_UNRESOLVED"])
    if negative_sources < 2:
        return result("TM_HOLD", "EVIDENCE_INCOMPLETE", ["NEGATIVE_EVIDENCE_CONVERGENCE_INSUFFICIENT"])

    return result("TM_PASS", "FALLBACK_HIGH_CONFIDENCE", ["REQUIRED_SCOPE_COMPLETE", "NO_MATERIAL_CONFLICT_DETECTED", "NEGATIVE_EVIDENCE_CONVERGED"])
