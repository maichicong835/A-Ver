#!/usr/bin/env python3
import json
from pathlib import Path

from decision import evaluate_tm_state
from similarity import analyze_word_mark_similarity

CANARIES = [
    {
        "candidate_key": "nursing-school-hard-but-damn",
        "wording": "I KNOW THEY SAID NURSING SCHOOL WAS HARD, BUT DAMN",
        "material_record": {
            "identifier": "90319838",
            "mark_text": "NURSING SCHOOL JEWELS",
            "goods_relatedness": "MATERIAL",
            "component_strength_state": "DISCLAIMED_COMPONENT",
            "evidence": {
                "official_component_strength_run_id": "34747615542",
                "official_component_strength_artifact_id": "10314457270",
                "machine_fact": "NURSING SCHOOL component officially disclaimed"
            }
        },
        "unresolved_dimensions": [
            "SEMANTIC_AND_COMMERCIAL_IMPRESSION",
            "PHONETIC_OR_SPELLING_WHEN_MATERIAL",
            "REQUIRED_QUERY_SCOPE"
        ]
    },
    {
        "candidate_key": "powered-by-yarn-and-chaos",
        "wording": "POWERED BY YARN AND CHAOS",
        "material_record": {
            "identifier": "88678935",
            "mark_text": "YARN",
            "goods_relatedness": "MATERIAL",
            "component_strength_state": "UNRESOLVED",
            "evidence": {
                "material_frontier_run_id": "34746827135",
                "material_frontier_artifact_id": "10313893571",
                "official_spot_verifier_state": "HOLD_CAPABILITY_AFTER_BOUNDED_RETRY"
            }
        },
        "unresolved_dimensions": [
            "SHARED_COMPONENT_STRENGTH",
            "SEMANTIC_AND_COMMERCIAL_IMPRESSION",
            "PHONETIC_OR_SPELLING_WHEN_MATERIAL",
            "REQUIRED_QUERY_SCOPE"
        ]
    }
]


def evaluate_canary(canary):
    record = canary["material_record"]
    similarity = analyze_word_mark_similarity(
        canary["wording"],
        record["mark_text"],
        record["component_strength_state"],
    )
    decision_state = {
        "material_positive_record_present": True,
        "record_binding_complete": True,
        "similarity_assessment": similarity["assessment"],
        "goods_relatedness_assessment": record["goods_relatedness"],
        "required_query_dimensions_complete": False,
        "resolver_scope_complete": False,
        "unresolved_dimensions": canary["unresolved_dimensions"],
        "negative_evidence_distinct_sources": 2,
        "scope_qualified_negative_evidence_distinct_sources": 0,
        "transport_blocked": False,
        "control_blocked": False,
        "source_discordance": False,
    }
    decision = evaluate_tm_state(decision_state)

    assert similarity["assessment"] == "UNRESOLVED", (canary["candidate_key"], similarity)
    assert decision["decision"] == "TM_HOLD", (canary["candidate_key"], decision)
    assert decision["legal_clearance_asserted"] is False
    assert decision["confidence_label"] == "EVIDENCE_INCOMPLETE"

    if canary["candidate_key"] == "nursing-school-hard-but-damn":
        assert "SHARED_COMPONENT_OFFICIALLY_DISCLAIMED_IN_BOUND_RECORD" in similarity["reason_codes"]
        assert "DISCLAIMER_DOES_NOT_BY_ITSELF_PROVE_NO_LIKELIHOOD_OF_CONFUSION" in similarity["reason_codes"]
    if canary["candidate_key"] == "powered-by-yarn-and-chaos":
        assert similarity["single_token_containment"] is True
        assert similarity["component_strength_state"] == "UNRESOLVED"

    return {
        "candidate_key": canary["candidate_key"],
        "wording": canary["wording"],
        "material_record": record,
        "similarity": similarity,
        "decision_input": decision_state,
        "decision": decision,
        "false_tm_pass_observed": decision["decision"] == "TM_PASS",
        "false_tm_kill_observed": decision["decision"] == "TM_KILL",
    }


def main():
    results = [evaluate_canary(c) for c in CANARIES]
    receipt = {
        "schema": "AVER_DEEP_DECISION_CANARY",
        "schema_version": "1.0",
        "scope": "EXISTING_TWO_DAILY7_HOLD_CANARIES_ONLY",
        "candidate_breadth_expanded": False,
        "resolver_transport_executed": False,
        "daily7_live_gate_authorized": False,
        "phase_state": "DEEP_CANARY_INTERPRETATION_PASS",
        "canaries": results,
        "all_decisions": [x["decision"]["decision"] for x in results],
        "false_tm_pass_observed": any(x["false_tm_pass_observed"] for x in results),
        "false_tm_kill_observed": any(x["false_tm_kill_observed"] for x in results),
        "required_query_scope_complete": False,
        "next_gate": "G4_SCOPE_COMPLETENESS_AND_DECISION"
    }
    assert receipt["all_decisions"] == ["TM_HOLD", "TM_HOLD"]
    assert receipt["false_tm_pass_observed"] is False
    assert receipt["false_tm_kill_observed"] is False
    assert receipt["required_query_scope_complete"] is False

    path = Path("artifacts/deep-decision")
    path.mkdir(parents=True, exist_ok=True)
    (path / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("AVER_DEEP_CANARY_INTERPRETATION_PASS")
    for result in results:
        print(result["candidate_key"], result["similarity"]["assessment"], result["decision"]["decision"])


if __name__ == "__main__":
    main()
