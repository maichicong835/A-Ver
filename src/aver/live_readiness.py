#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path


def _pass(gate_id, evidence):
    return {"gate_id": gate_id, "state": "PASS", "evidence": evidence, "blockers": []}


def _block(gate_id, blockers, evidence=None):
    return {"gate_id": gate_id, "state": "BLOCKED", "evidence": evidence or {}, "blockers": list(blockers)}


def evaluate(current, engine, policy, state, *, candidate_sha, authority_contract_pass, contract_matrix_pass):
    gates=[]

    g1_ok=(
        authority_contract_pass
        and current.get("canonical_repository")=="maichicong835/A-Ver"
        and current.get("canonical_branch")=="main"
        and current.get("status")=="PRODUCTION_APPROVED_SCOPED"
        and engine.get("mode")=="PRODUCTION_SCOPED"
        and current.get("external_side_effects_authorized") is False
        and engine.get("interface_contract",{}).get("receipt_must_bind_exact_engine_commit") is True
        and state.get("state_is_evidence_index_not_authorization") is True
        and state.get("live_authorized") is False
    )
    g1_evidence={
        "candidate_sha":candidate_sha,
        "authority_contract_on_candidate_sha":authority_contract_pass,
        "repository":current.get("canonical_repository"),
        "branch":current.get("canonical_branch"),
        "engine_version":current.get("engine_version"),
        "external_side_effects_authorized":current.get("external_side_effects_authorized"),
        "evidence_state_is_not_authorization":state.get("state_is_evidence_index_not_authorization")
    }
    gates.append(_pass("G1_AUTHORITY_AND_ENGINE_IDENTITY",g1_evidence) if g1_ok else _block("G1_AUTHORITY_AND_ENGINE_IDENTITY",["AUTHORITY_CONTRACT_OR_ENGINE_IDENTITY_NOT_PROVEN"],g1_evidence))

    gates.append(_pass("G2_DECISION_CONTRACT_INTEGRITY",{
        "contract_matrix_on_candidate_sha":True,
        "scope_qualified_negative_convergence_required":True
    }) if contract_matrix_pass else _block("G2_DECISION_CONTRACT_INTEGRITY",["CONTRACT_MATRIX_NOT_PROVEN_ON_CANDIDATE_SHA"]))

    deep=state.get("deep_interpretation_closure") or {}
    deep_required={
        "material_frontier_machine_pass":True,
        "single_token_false_kill_guard_machine_pass":True,
        "official_component_strength_evidence_machine_pass":True,
        "required_query_plan_machine_pass":True,
        "deep_canary_interpretation_complete":True
    }
    deep_missing=[k for k,v in deep_required.items() if deep.get(k) is not v]
    gates.append(_pass("G3_DEEP_TM_INTERPRETATION",deep) if not deep_missing else _block("G3_DEEP_TM_INTERPRETATION",[f"MISSING_OR_UNPROVEN:{k}" for k in deep_missing],deep))

    scope=state.get("decision_scope_closure") or {}
    g4b=scope.get("g4b_subgates") or {}
    scope_required={
        "required_query_scope_semantics_complete":True,
        "class016_clean_pass_path_machine_proven":True,
        "scope_qualified_negative_convergence_enforced":True,
        "capability_failure_separated_from_candidate_risk":True,
        "existing_canaries_deterministic_for_correct_reason":True
    }
    g4b_required={
        "official_uspto_multiword_exact_semantics_machine_proven":True,
        "second_independent_multiword_negative_source_machine_proven":True,
        "multiword_scope_qualified_negative_convergence_machine_proven":True,
        "production_reachable_clean_pass_machine_proven":True
    }
    scope_missing=[k for k,v in scope_required.items() if scope.get(k) is not v]
    g4b_missing=[k for k,v in g4b_required.items() if g4b.get(k) is not v]
    g4_blockers=[f"MISSING_OR_UNPROVEN:{k}" for k in scope_missing]+[f"MISSING_OR_UNPROVEN:G4B:{k}" for k in g4b_missing]
    g4_evidence={**scope,"governor_explicit_g4b_subgate_check":True}
    gates.append(_pass("G4_SCOPE_COMPLETENESS_AND_DECISION",g4_evidence) if not g4_blockers else _block("G4_SCOPE_COMPLETENESS_AND_DECISION",g4_blockers,g4_evidence))

    shadow=state.get("daily7_deep_shadow_closure") or {}
    shadow_ok=(
        shadow.get("state")=="PASS_CLOSED"
        and shadow.get("aver_pin_sha")==candidate_sha
        and shadow.get("request_schema_validated") is True
        and shadow.get("receipt_schema_validated") is True
        and shadow.get("caller_mutation_observed") is False
        and shadow.get("false_tm_pass_observed") is False
        and shadow.get("false_tm_kill_observed") is False
    )
    gates.append(_pass("G5_DAILY7_DEEP_SHADOW",shadow) if shadow_ok else _block("G5_DAILY7_DEEP_SHADOW",["DEEP_SHADOW_NOT_MACHINE_PROVEN_ON_EXACT_CANDIDATE_PIN"],shadow))

    rehearsal=state.get("live_boundary_rehearsal_closure") or {}
    rehearsal_ok=(
        rehearsal.get("state")=="PASS_CLOSED"
        and rehearsal.get("aver_pin_sha")==candidate_sha
        and rehearsal.get("mutation_enabled") is False
        and rehearsal.get("pass_kill_hold_handling_proven") is True
        and rehearsal.get("fail_closed_boundary_proven") is True
    )
    gates.append(_pass("G6_LIVE_BOUNDARY_REHEARSAL",rehearsal) if rehearsal_ok else _block("G6_LIVE_BOUNDARY_REHEARSAL",["LIVE_BOUNDARY_REHEARSAL_NOT_MACHINE_PROVEN_ON_EXACT_CANDIDATE_PIN"],rehearsal))

    blocking=[g for g in gates if g["state"]!="PASS"]
    terminal="READY_FOR_EXPLICIT_LIVE_AUTHORIZATION" if not blocking else "BLOCKED"
    return {
        "schema":"AVER_DAILY7_LIVE_READINESS_RECEIPT",
        "schema_version":"1.0",
        "candidate_sha":candidate_sha,
        "terminal_state":terminal,
        "first_blocking_gate":blocking[0]["gate_id"] if blocking else None,
        "workflow_success_implies_live_ready":False,
        "aver_may_self_authorize_daily7_live":False,
        "g7_explicit_live_authorization_required_after_ready":True,
        "gates":gates,
        "live_authorized":False
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--candidate-sha",default=os.getenv("GITHUB_SHA","UNBOUND"))
    parser.add_argument("--authority-contract-pass",action="store_true")
    parser.add_argument("--contract-matrix-pass",action="store_true")
    parser.add_argument("--output",default="artifacts/live-readiness/receipt.json")
    args=parser.parse_args()

    current=json.loads(Path("CURRENT.json").read_text())
    engine=json.loads(Path("spec/engine.json").read_text())
    policy=json.loads(Path("spec/live-readiness.json").read_text())
    state=json.loads(Path("spec/live-readiness-state.json").read_text())
    receipt=evaluate(current,engine,policy,state,candidate_sha=args.candidate_sha,authority_contract_pass=args.authority_contract_pass,contract_matrix_pass=args.contract_matrix_pass)

    assert receipt["terminal_state"] in policy["terminal_states"]
    assert receipt["live_authorized"] is False
    assert receipt["aver_may_self_authorize_daily7_live"] is False
    if receipt["terminal_state"]=="READY_FOR_EXPLICIT_LIVE_AUTHORIZATION":
        assert all(g["state"]=="PASS" for g in receipt["gates"])
        assert receipt["first_blocking_gate"] is None
    else:
        assert receipt["first_blocking_gate"] is not None

    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("AVER_LIVE_READINESS_GOVERNOR_PASS")
    print("terminal_state=",receipt["terminal_state"])
    print("first_blocking_gate=",receipt["first_blocking_gate"])
    for gate in receipt["gates"]:
        print(gate["gate_id"],gate["state"],",".join(gate["blockers"]))


if __name__=="__main__":
    main()
