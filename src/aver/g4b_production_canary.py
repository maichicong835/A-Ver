#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
from aver.decision import evaluate_tm_state
from aver.query_plan import build_query_plan, normalize_wording
from aver.resolvers import TrademarkiaResolver
from aver.scope_semantics import resolve_dimension, evaluate_required_scope
from aver.uspto_fieldtag_direct_canary import run_case as run_uspto_case

PHRASE="Mildly Lost, Weirdly Optimistic"


def uspto_zero(browser,query):
    rec=run_uspto_case(browser,{"name":query,"query":query,"expected":"ZERO"})
    return rec, rec.get("state")=="PASS" and (rec.get("terminal") or {}).get("native_zero") is True


def trademarkia_quoted_zero(resolver,query):
    quoted='"'+query.replace('"','').strip()+'"'
    rec=resolver.search(quoted,"OPAQUE_ZERO")
    return rec, rec.get("state")=="CAPABILITY_PASS" and (rec.get("terminal_result") or {}).get("terminal")=="ZERO_RESULTSET"


def official_exact_query(text):
    return 'CM:"'+text.replace('"','').strip()+'"'


def official_expanded_query(text):
    toks=re.findall(r"[a-z0-9]+",text.lower())
    return "CM:("+" AND ".join(f"/.*{re.escape(t)}.*/" for t in toks)+")"


def main():
    out={
        "schema":"AVER_G4B_PRODUCTION_SHAPED_CANARY",
        "production_shaped_canary":True,"fixed_phrase":True,"phrase":PHRASE,
        "phrase_replacement_on_failure_forbidden":True,"daily7_candidate":False,
        "daily7_live_gate_authorized":False,"may_close_g4b_only_if_full_scope_tm_pass":True,
        "trademarkia_strategy":"QUOTED_MULTIWORD_WITH_PER_QUERY_STABLE_BINDING_AND_NATIVE_ZERO",
        "trademarkia_generalization_beyond_observed_queries_forbidden":True,
        "phase_state":"G4B_PRODUCTION_SHAPED_PARTIAL","evidence":{},
    }
    plan=build_query_plan(PHRASE,[]); out["query_plan"]=plan
    cores=plan["CORE_DOMINANT_TOKEN"]["queries"]
    if not cores or not plan["PHONETIC_OR_SPELLING_WHEN_MATERIAL"]["queries"]:
        out["failure_signature"]="PRODUCTION_QUERY_PLAN_INCOMPLETE"
    else:
        executable=os.getenv("AVER_BROWSER_EXECUTABLE") or None
        with sync_playwright() as p:
            launch={"headless":True}
            if executable: launch["executable_path"]=executable
            browser=p.chromium.launch(**launch); tm=TrademarkiaResolver(browser)
            usp_exact,usp_exact_ok=uspto_zero(browser,official_exact_query(PHRASE))
            tm_exact,tm_exact_ok=trademarkia_quoted_zero(tm,PHRASE)
            out["evidence"]["exact"]={"uspto":usp_exact,"trademarkia_quoted":tm_exact}
            core_rows=[]; core_ok=True; partial_ok=True; tm_core_all_zero=True
            for core in cores:
                usp_core,usp_core_ok=uspto_zero(browser,official_exact_query(core))
                tm_core,tm_core_ok=trademarkia_quoted_zero(tm,core)
                usp_partial,usp_partial_ok=uspto_zero(browser,official_expanded_query(core))
                core_rows.append({"core":core,"uspto_exact":usp_core,"trademarkia_quoted":tm_core,
                                  "uspto_expanded":usp_partial,"core_zero":usp_core_ok and tm_core_ok,
                                  "expanded_zero":usp_partial_ok})
                core_ok=core_ok and usp_core_ok and tm_core_ok
                partial_ok=partial_ok and usp_partial_ok
                tm_core_all_zero=tm_core_all_zero and tm_core_ok
            out["evidence"]["cores"]=core_rows
            phon_query=plan["PHONETIC_OR_SPELLING_WHEN_MATERIAL"]["queries"][0]
            usp_phon,usp_phon_ok=uspto_zero(browser,phon_query)
            out["evidence"]["phonetic_spelling"]={"query":phon_query,"uspto":usp_phon,"negative":usp_phon_ok}
            browser.close()

        exact_ok=usp_exact_ok and tm_exact_ok
        normalized_equiv=normalize_wording(PHRASE)==plan["NORMALIZED_EXACT"]["queries"][0]
        related_goods_ok=usp_exact_ok and core_ok and partial_ok and usp_phon_ok
        dimensions=[
            resolve_dimension(dimension="EXACT",execution_state="EXECUTED",evidence_polarity="NEGATIVE",negative_semantics_scope_ok=exact_ok),
            resolve_dimension(dimension="NORMALIZED_EXACT",execution_state="EXECUTED",evidence_polarity="NEGATIVE",negative_semantics_scope_ok=exact_ok and normalized_equiv),
            resolve_dimension(dimension="CORE_DOMINANT_TOKEN",execution_state="EXECUTED",evidence_polarity="NEGATIVE",negative_semantics_scope_ok=core_ok),
            resolve_dimension(dimension="EXPANDED_PARTIAL",execution_state="EXECUTED",evidence_polarity="NEGATIVE",negative_semantics_scope_ok=partial_ok),
            resolve_dimension(dimension="PHONETIC_OR_SPELLING_WHEN_MATERIAL",execution_state="EXECUTED",evidence_polarity="NEGATIVE",negative_semantics_scope_ok=usp_phon_ok,material_trigger=True),
            resolve_dimension(dimension="RELATED_GOODS_REVIEW",execution_state="EXECUTED",evidence_polarity="NEGATIVE",negative_semantics_scope_ok=related_goods_ok),
        ]
        scope=evaluate_required_scope(dimensions); out["dimension_records"]=dimensions; out["scope"]=scope
        two_source_candidate_negative=usp_exact_ok and tm_exact_ok and tm_core_all_zero
        decision_input={"material_positive_record_present":False,"record_binding_complete":True,
            "similarity_assessment":"NON_MATERIAL","goods_relatedness_assessment":"NON_MATERIAL",
            "required_query_dimensions_complete":scope["negative_scope_complete"],"resolver_scope_complete":scope["negative_scope_complete"],
            "unresolved_dimensions":scope["unresolved_dimensions"],"negative_evidence_distinct_sources":2,
            "scope_qualified_negative_evidence_distinct_sources":2 if two_source_candidate_negative else 0,
            "transport_blocked":False,"control_blocked":False,"source_discordance":False}
        decision=evaluate_tm_state(decision_input); out["decision_input"]=decision_input; out["decision"]=decision
        if scope["negative_scope_complete"] and two_source_candidate_negative and decision.get("decision")=="TM_PASS":
            out["phase_state"]="G4B_PRODUCTION_SHAPED_TM_PASS_PROVEN"

    path=Path("artifacts/g4b-production"); path.mkdir(parents=True,exist_ok=True)
    (path/"receipt.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print("phase_state=",out["phase_state"]); print("cores=",cores)
    print("decision=",(out.get("decision") or {}).get("decision")); print("unresolved=",(out.get("scope") or {}).get("unresolved_dimensions"))
    if out["phase_state"]!="G4B_PRODUCTION_SHAPED_TM_PASS_PROVEN": raise SystemExit("G4B_PRODUCTION_SHAPED_CANARY_NOT_PASS")

if __name__=="__main__": main()
