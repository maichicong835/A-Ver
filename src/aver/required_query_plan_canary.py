#!/usr/bin/env python3
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

from aver.material_record_priority import prioritize_material_records
from aver.query_plan import build_query_plan
from aver.record_interpretation import discover_record_anchors_from_page
from aver.resolvers import TrademarkiaResolver

CANARIES=[
    {"candidate_key":"nursing-school-hard-but-damn","wording":"I KNOW THEY SAID NURSING SCHOOL WAS HARD, BUT DAMN"},
    {"candidate_key":"powered-by-yarn-and-chaos","wording":"POWERED BY YARN AND CHAOS"},
]


def _terminal(rec):
    return (rec.get("terminal_result") or {}).get("terminal")


def main():
    out={"schema":"AVER_REQUIRED_QUERY_PLAN_CANARY","shadow_only":True,"candidate_breadth_expanded":False,"tm_decision_authorized":False,"daily7_live_gate_authorized":False,"phase_state":"QUERY_PLAN_EXECUTION_PARTIAL","canaries":[]}
    executable=os.getenv("AVER_BROWSER_EXECUTABLE") or None
    with sync_playwright() as p:
        launch={"headless":True}
        if executable: launch["executable_path"]=executable
        browser=p.chromium.launch(**launch)
        resolver=TrademarkiaResolver(browser)
        for c in CANARIES:
            broad=resolver.search(c["wording"],"FUZZY_RECALL",post_terminal_observer=lambda page,terminal: discover_record_anchors_from_page(page,limit=12))
            anchors=broad.get("post_terminal_observation") or []
            queue=prioritize_material_records(c["wording"],anchors,primary_class="016",merch_adjacent_classes=("025",),limit=8)
            plan=build_query_plan(c["wording"],queue)
            executions=[]
            seen={}
            def run_broad(stage,query):
                key=query.strip().upper()
                if key in seen:
                    return {"stage":stage,"query":query,"execution":"ALIASED_TO_PRIOR_QUERY","aliased_to":seen[key],"positive_recall_resolved":True,"federal_exact_negative_semantics_proven":False}
                rec=resolver.search(query,"FUZZY_RECALL")
                term=_terminal(rec)
                resolved=term in ("POSITIVE_RESULTSET","ZERO_RESULTSET")
                seen[key]=stage
                return {"stage":stage,"query":query,"execution":"EXECUTED","resolver_state":rec.get("state"),"terminal":term,"positive_recall_resolved":resolved,"federal_exact_negative_semantics_proven":False,"evidence_hash":rec.get("body_sha256"),"failure_signature":rec.get("failure_signature")}

            exact=run_broad("EXACT",c["wording"]); executions.append(exact)
            for q in plan["NORMALIZED_EXACT"]["queries"]:
                executions.append(run_broad("NORMALIZED_EXACT",q))
            for q in plan["CORE_DOMINANT_TOKEN"]["queries"]:
                executions.append(run_broad("CORE_DOMINANT_TOKEN",q))
            for q in plan["EXPANDED_PARTIAL"]["queries"]:
                executions.append(run_broad("EXPANDED_PARTIAL",q))

            query_execution_ok=bool(queue and plan["CORE_DOMINANT_TOKEN"]["queries"] and all(x.get("positive_recall_resolved") is True for x in executions))
            dimension_states={
                "EXACT":"EXECUTED_NEGATIVE_SEMANTICS_UNPROVEN",
                "NORMALIZED_EXACT":"EXECUTED_NEGATIVE_SEMANTICS_UNPROVEN",
                "CORE_DOMINANT_TOKEN":"EXECUTED_POSITIVE_RECALL_ONLY",
                "EXPANDED_PARTIAL":"EXECUTED_POSITIVE_RECALL_ONLY",
                "PHONETIC_OR_SPELLING_WHEN_MATERIAL":"UNRESOLVED_POLICY_NOT_MACHINE_PROVEN",
                "RELATED_GOODS_REVIEW":"PARTIAL_BOUND_FRONTIER_G0_G1_WITH_G2_G4_NOT_UNIFORMLY_COMPLETE",
            }
            unresolved=[k for k,v in dimension_states.items() if not v.startswith("RESOLVED")]
            passed=bool(broad.get("state")=="CAPABILITY_PASS" and query_execution_ok and unresolved)
            out["canaries"].append({**c,"query_plan":plan,"executions":executions,"dimension_states":dimension_states,"required_query_dimensions_complete":False,"federal_negative_clearance_scope_complete":False,"unresolved_dimensions":unresolved,"pass":passed})
        browser.close()
    if len(out["canaries"])==2 and all(x["pass"] for x in out["canaries"]):
        out["phase_state"]="QUERY_PLAN_EXECUTION_PASS_SCOPE_INCOMPLETE"
    path=Path("artifacts/query-plan"); path.mkdir(parents=True,exist_ok=True)
    (path/"receipt.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print("phase_state=",out["phase_state"])
    for c in out["canaries"]:
        print(c["candidate_key"],c["query_plan"]["CORE_DOMINANT_TOKEN"]["queries"],c["unresolved_dimensions"])
    if out["phase_state"]!="QUERY_PLAN_EXECUTION_PASS_SCOPE_INCOMPLETE":
        raise SystemExit("QUERY_PLAN_EXECUTION_NOT_PROVEN")

if __name__=="__main__": main()
