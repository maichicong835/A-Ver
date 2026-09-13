#!/usr/bin/env python3
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

from aver.material_record_priority import prioritize_material_records
from aver.record_interpretation import discover_record_anchors_from_page
from aver.resolvers import TrademarkiaResolver

CANARIES=[
    {
        "candidate_key":"nursing-school-hard-but-damn",
        "wording":"I KNOW THEY SAID NURSING SCHOOL WAS HARD, BUT DAMN",
        "must_prioritize_any":["90319838","98580761"],
        "must_see_in_queue":["90319838"],
    },
    {
        "candidate_key":"powered-by-yarn-and-chaos",
        "wording":"POWERED BY YARN AND CHAOS",
        "must_prioritize_any":["88678935","87132994"],
        "must_see_in_queue":["90072046"],
    },
]


def main():
    out={"schema":"AVER_MATERIAL_RECORD_PRIORITY_CANARY","shadow_only":True,"candidate_breadth_expanded":False,"tm_decision_authorized":False,"phase_state":"MATERIAL_RECORD_PRIORITY_PARTIAL","canaries":[]}
    executable=os.getenv("AVER_BROWSER_EXECUTABLE") or None
    with sync_playwright() as p:
        launch={"headless":True}
        if executable: launch["executable_path"]=executable
        browser=p.chromium.launch(**launch)
        resolver=TrademarkiaResolver(browser)
        for c in CANARIES:
            rec=resolver.search(c["wording"],"FUZZY_RECALL",post_terminal_observer=lambda page,terminal: discover_record_anchors_from_page(page,limit=12))
            anchors=rec.get("post_terminal_observation") or []
            queue=prioritize_material_records(c["wording"],anchors,primary_class="016",merch_adjacent_classes=("025",),limit=8)
            ids=[x["identifier"] for x in queue]
            top4=set(ids[:4])
            pass_any=bool(top4 & set(c["must_prioritize_any"]))
            pass_seen=all(x in ids for x in c["must_see_in_queue"])
            no_decisions=all(x.get("safety_decision") is None and x.get("legal_clearance_asserted") is False for x in queue)
            passed=bool(rec.get("state")=="CAPABILITY_PASS" and rec.get("post_terminal_observer_state")=="OBSERVED" and queue and pass_any and pass_seen and no_decisions)
            out["canaries"].append({**c,"resolver_state":rec.get("state"),"observer_state":rec.get("post_terminal_observer_state"),"anchor_count":len(anchors),"priority_queue":queue,"top4_material_candidate_seen":pass_any,"known_bound_record_retained":pass_seen,"triage_does_not_decide_safety":no_decisions,"pass":passed})
        browser.close()
    if len(out["canaries"])==2 and all(x["pass"] for x in out["canaries"]):
        out["phase_state"]="MATERIAL_RECORD_PRIORITY_PASS"
    path=Path("artifacts/deep-interpretation"); path.mkdir(parents=True,exist_ok=True)
    (path/"priority-receipt.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print("phase_state=",out["phase_state"])
    for c in out["canaries"]:
        print(c["candidate_key"],[(x["identifier"],x["mark_text"],x["classes"],x["priority_score"]) for x in c["priority_queue"][:5]])
    if out["phase_state"]!="MATERIAL_RECORD_PRIORITY_PASS":
        raise SystemExit("MATERIAL_RECORD_PRIORITY_NOT_PASS")

if __name__=="__main__": main()
