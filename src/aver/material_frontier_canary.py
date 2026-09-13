#!/usr/bin/env python3
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

from aver.goods_relatedness import evaluate_g0_g4
from aver.material_record_priority import prioritize_material_records
from aver.record_detail_browser import capture_expanded_trademarkia_record
from aver.record_interpretation import discover_record_anchors_from_page
from aver.resolvers import TrademarkiaResolver
from aver.similarity import analyze_word_mark_similarity

CANARIES = [
    {"candidate_key":"nursing-school-hard-but-damn","wording":"I KNOW THEY SAID NURSING SCHOOL WAS HARD, BUT DAMN"},
    {"candidate_key":"powered-by-yarn-and-chaos","wording":"POWERED BY YARN AND CHAOS"},
]
INTENDED_GOODS={"primary_class":"016","description":"Decorative adhesive stickers and printed stickers for personal items"}


def main():
    out={"schema":"AVER_MATERIAL_FRONTIER_CANARY","shadow_only":True,"candidate_breadth_expanded":False,"tm_decision_authorized":False,"daily7_live_gate_authorized":False,"phase_state":"MATERIAL_FRONTIER_PARTIAL","canaries":[]}
    executable=os.getenv("AVER_BROWSER_EXECUTABLE") or None
    with sync_playwright() as p:
        launch={"headless":True}
        if executable:
            launch["executable_path"]=executable
        browser=p.chromium.launch(**launch)
        resolver=TrademarkiaResolver(browser)
        for c in CANARIES:
            rec=resolver.search(c["wording"],"FUZZY_RECALL",post_terminal_observer=lambda page,terminal: discover_record_anchors_from_page(page,limit=12))
            anchors=rec.get("post_terminal_observation") or []
            queue=prioritize_material_records(c["wording"],anchors,primary_class="016",merch_adjacent_classes=("025",),limit=8)
            frontier=[]
            for item in queue[:2]:
                expected_class=item["classes"][0] if item.get("classes") else None
                direct=resolver.bind_record_url(item["record_url"],item["identifier"],item["mark_text"],expected_class)
                expanded=capture_expanded_trademarkia_record(browser,item["record_url"])
                detail=(expanded or {}).get("structured_record_detail") or {}
                goods=evaluate_g0_g4(INTENDED_GOODS,detail) if expanded and expanded.get("state")=="EXPANDED_RECORD_PASS" else None
                similarity=analyze_word_mark_similarity(c["wording"],item["mark_text"],"UNRESOLVED")
                bound_ok=bool(
                    direct and direct.get("state")=="CAPABILITY_PASS"
                    and expanded and expanded.get("state")=="EXPANDED_RECORD_PASS"
                    and detail.get("serial_number")==item["identifier"]
                    and detail.get("registration_number")
                )
                frontier.append({
                    "priority":item,
                    "direct_record_binding":direct,
                    "expanded_record_detail":expanded,
                    "goods_relatedness_g0_g4":goods,
                    "similarity_analysis":similarity,
                    "record_machine_bound":bound_ok,
                    "tm_decision":None,
                    "legal_clearance_asserted":False,
                })
            passed=bool(
                rec.get("state")=="CAPABILITY_PASS"
                and len(frontier)==2
                and all(x["record_machine_bound"] for x in frontier)
                and all(x["tm_decision"] is None and x["legal_clearance_asserted"] is False for x in frontier)
            )
            out["canaries"].append({**c,"priority_queue":queue,"frontier":frontier,"pass":passed})
        browser.close()
    if len(out["canaries"])==2 and all(x["pass"] for x in out["canaries"]):
        out["phase_state"]="MATERIAL_FRONTIER_PASS"
    path=Path("artifacts/deep-interpretation")
    path.mkdir(parents=True,exist_ok=True)
    (path/"frontier-receipt.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print("phase_state=",out["phase_state"])
    for c in out["canaries"]:
        summary=[]
        for x in c["frontier"]:
            summary.append((x["priority"]["identifier"],x["priority"]["mark_text"],x["similarity_analysis"]["assessment"],(x["goods_relatedness_g0_g4"] or {}).get("assessment")))
        print(c["candidate_key"],summary)
    if out["phase_state"]!="MATERIAL_FRONTIER_PASS":
        raise SystemExit("MATERIAL_FRONTIER_NOT_PASS")

if __name__=="__main__":
    main()
