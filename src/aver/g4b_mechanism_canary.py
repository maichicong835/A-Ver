#!/usr/bin/env python3
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

from aver.decision import evaluate_tm_state
from aver.resolvers import TrademarkiaResolver
from aver.scope_semantics import resolve_dimension, evaluate_required_scope
from aver.uspto_fieldtag_direct_canary import run_case as run_uspto_case

PHRASE = "QZXJVMRKPLNX VQTKRMNZXJQW"
TOKENS = ["QZXJVMRKPLNX", "VQTKRMNZXJQW"]


def uspto_zero(browser, query):
    rec = run_uspto_case(browser, {"name": query, "query": query, "expected": "ZERO"})
    return rec, rec.get("state") == "PASS" and (rec.get("terminal") or {}).get("native_zero") is True


def trademarkia_zero(resolver, query):
    rec = resolver.search(query, "OPAQUE_ZERO")
    return rec, rec.get("state") == "CAPABILITY_PASS" and (rec.get("terminal_result") or {}).get("terminal") == "ZERO_RESULTSET"


def main():
    out = {
        "schema": "AVER_G4B_MECHANISM_CANARY",
        "synthetic_mechanism_only": True,
        "production_shaped_canary": False,
        "may_close_g4b": False,
        "daily7_candidate_queries_executed": False,
        "daily7_live_gate_authorized": False,
        "phase_state": "G4B_MECHANISM_PARTIAL",
        "phrase": PHRASE,
        "evidence": {},
    }

    executable = os.getenv("AVER_BROWSER_EXECUTABLE") or None
    with sync_playwright() as p:
        launch = {"headless": True}
        if executable:
            launch["executable_path"] = executable
        browser = p.chromium.launch(**launch)
        tm = TrademarkiaResolver(browser)

        usp_full, usp_full_ok = uspto_zero(browser, f'CM:"{PHRASE}"')
        tm_full, tm_full_ok = trademarkia_zero(tm, PHRASE)
        out["evidence"]["uspto_exact"] = usp_full
        out["evidence"]["trademarkia_full"] = tm_full

        token_rows = []
        all_token_both_zero = True
        all_tm_token_zero = True
        for token in TOKENS:
            usp, usp_ok = uspto_zero(browser, f"CM:{token}")
            tmr, tm_ok = trademarkia_zero(tm, token)
            token_rows.append({"token": token, "uspto": usp, "trademarkia": tmr, "uspto_zero": usp_ok, "trademarkia_zero": tm_ok})
            all_token_both_zero = all_token_both_zero and usp_ok and tm_ok
            all_tm_token_zero = all_tm_token_zero and tm_ok
        out["evidence"]["tokens"] = token_rows
        browser.close()

    dimensions = [
        resolve_dimension(dimension="EXACT", execution_state="EXECUTED", evidence_polarity="NEGATIVE", negative_semantics_scope_ok=usp_full_ok and tm_full_ok),
        resolve_dimension(dimension="NORMALIZED_EXACT", execution_state="EXECUTED", evidence_polarity="NEGATIVE", negative_semantics_scope_ok=usp_full_ok and tm_full_ok),
        resolve_dimension(dimension="CORE_DOMINANT_TOKEN", execution_state="EXECUTED", evidence_polarity="NEGATIVE", negative_semantics_scope_ok=all_token_both_zero),
        resolve_dimension(dimension="EXPANDED_PARTIAL", execution_state="EXECUTED", evidence_polarity="NEGATIVE", negative_semantics_scope_ok=tm_full_ok and all_tm_token_zero),
        resolve_dimension(dimension="PHONETIC_OR_SPELLING_WHEN_MATERIAL", execution_state="EXECUTED", material_trigger=False),
        resolve_dimension(dimension="RELATED_GOODS_REVIEW", execution_state="EXECUTED", evidence_polarity="NEGATIVE", negative_semantics_scope_ok=usp_full_ok and tm_full_ok and all_token_both_zero),
    ]
    scope = evaluate_required_scope(dimensions)
    out["dimension_records"] = dimensions
    out["scope"] = scope

    decision_input = {
        "material_positive_record_present": False,
        "record_binding_complete": True,
        "similarity_assessment": "NON_MATERIAL",
        "goods_relatedness_assessment": "NON_MATERIAL",
        "required_query_dimensions_complete": scope["negative_scope_complete"],
        "resolver_scope_complete": scope["negative_scope_complete"],
        "unresolved_dimensions": scope["unresolved_dimensions"],
        "negative_evidence_distinct_sources": 2,
        "scope_qualified_negative_evidence_distinct_sources": 2 if usp_full_ok and tm_full_ok else 0,
        "transport_blocked": False,
        "control_blocked": False,
        "source_discordance": False,
    }
    decision = evaluate_tm_state(decision_input)
    out["decision_input"] = decision_input
    out["decision"] = decision

    if scope["negative_scope_complete"] and decision.get("decision") == "TM_PASS":
        out["phase_state"] = "G4B_MECHANISM_TM_PASS_PROVEN"

    path = Path("artifacts/g4b-mechanism")
    path.mkdir(parents=True, exist_ok=True)
    (path / "receipt.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    print("phase_state=", out["phase_state"])
    print("negative_scope_complete=", scope["negative_scope_complete"])
    print("decision=", decision.get("decision"))
    if out["phase_state"] != "G4B_MECHANISM_TM_PASS_PROVEN":
        raise SystemExit("G4B_MECHANISM_NOT_PROVEN")


if __name__ == "__main__":
    main()
