#!/usr/bin/env python3
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

from aver.goods_relatedness import evaluate_g0_g4
from aver.record_detail_browser import capture_expanded_trademarkia_record
from aver.record_details import parse_trademarkia_record_detail
from aver.record_interpretation import bind_record_anchor, discover_record_anchors_from_page
from aver.resolvers import TrademarkiaResolver

CANARIES = [
    {"candidate_key":"nursing-school-hard-but-damn","wording":"I KNOW THEY SAID NURSING SCHOOL WAS HARD, BUT DAMN","expected_mark":"NURSING SCHOOL JEWELS","expected_serial":"90319838","expected_class":"016","expected_goods_token":"Notebooks","expanded_goods_token":"Stickers","expected_goods_assessment":"MATERIAL"},
    {"candidate_key":"powered-by-yarn-and-chaos","wording":"POWERED BY YARN AND CHAOS","expected_mark":"CHAOS BY ELSIE","expected_serial":"90072046","expected_class":"018","expected_goods_token":"Handbags","expanded_goods_token":"Handbags","expected_goods_assessment":"UNRESOLVED"}
]

INTENDED_GOODS={
    "primary_class":"016",
    "description":"Decorative adhesive stickers and printed stickers for personal items",
}


def main():
    output={"schema":"AVER_DEEP_INTERPRETATION_CANARY_RECEIPT","shadow_only":True,"candidate_breadth_expanded":False,"tm_decision_authorized":False,"daily7_live_gate_authorized":False,"canaries":[],"phase_state":"G0_G1_GOODS_RELATEDNESS_PARTIAL"}
    executable=os.getenv("AVER_BROWSER_EXECUTABLE") or None
    with sync_playwright() as p:
        launch={"headless":True}
        if executable: launch["executable_path"]=executable
        browser=p.chromium.launch(**launch)
        resolver=TrademarkiaResolver(browser)
        for c in CANARIES:
            rec=resolver.search(c["wording"],"FUZZY_RECALL",post_terminal_observer=lambda page,terminal: discover_record_anchors_from_page(page,limit=12))
            anchors=rec.get("post_terminal_observation") or []
            target=next((x for x in anchors if x.get("identifier")==c["expected_serial"]),None)
            bound=bind_record_anchor(target.get("container_text", ""),c["expected_mark"],c["expected_serial"],c["expected_class"]) if target else None
            atomic_class_pass=bool(bound and bound.get("classes")==[c["expected_class"]])
            direct=resolver.bind_record_url(target.get("record_url"),c["expected_serial"],c["expected_mark"],c["expected_class"]) if target else None
            direct_pass=bool(direct and direct.get("state")=="CAPABILITY_PASS" and direct.get("serial_seen") is True and direct.get("mark_seen") is True and direct.get("expected_class_seen") is True and direct.get("status"))
            structured=parse_trademarkia_record_detail((direct or {}).get("body_excerpt", "")) if direct else None
            class_detail=next((x for x in (structured or {}).get("class_details",[]) if x.get("class_code")==c["expected_class"]),None)
            structured_pass=bool(structured and structured.get("structured_detail_complete") is True and structured.get("serial_number")==c["expected_serial"] and structured.get("registration_number") and c["expected_class"] in structured.get("class_codes",[]) and class_detail and c["expected_goods_token"].lower() in (class_detail.get("goods_services_text") or "").lower())
            expanded=capture_expanded_trademarkia_record(browser,target.get("record_url")) if target else None
            expanded_structured=(expanded or {}).get("structured_record_detail") or {}
            expanded_class=next((x for x in expanded_structured.get("class_details",[]) if x.get("class_code")==c["expected_class"]),None)
            expanded_pass=bool(expanded and expanded.get("state")=="EXPANDED_RECORD_PASS" and expanded_structured.get("serial_number")==c["expected_serial"] and expanded_structured.get("registration_number") and expanded_class and c["expanded_goods_token"].lower() in (expanded_class.get("goods_services_text") or "").lower())
            goods=evaluate_g0_g4(INTENDED_GOODS, expanded_structured) if expanded_pass else None
            goods_pass=bool(
                goods
                and goods.get("g0_g1_resolved") is True
                and goods.get("g2_g4_resolved") is False
                and goods.get("assessment")==c["expected_goods_assessment"]
                and goods.get("legal_clearance_asserted") is False
                and goods.get("axes",{}).get("G0_CLASS_OVERLAP",{}).get("state")=="RESOLVED"
                and goods.get("axes",{}).get("G1_EXPLICIT_GOODS_OVERLAP",{}).get("state")=="RESOLVED"
            )
            passed=bool(rec.get("state")=="CAPABILITY_PASS" and (rec.get("terminal_result") or {}).get("terminal")=="POSITIVE_RESULTSET" and rec.get("post_terminal_observer_state")=="OBSERVED" and target and bound and bound.get("bound") is True and atomic_class_pass and direct_pass and structured_pass and expanded_pass and goods_pass)
            output["canaries"].append({**c,"resolver_state":rec.get("state"),"terminal":(rec.get("terminal_result") or {}).get("terminal"),"observer_state":rec.get("post_terminal_observer_state"),"anchor_count":len(anchors),"expected_anchor_found":target is not None,"expected_anchor":target,"record_binding":bound,"atomic_class_pass":atomic_class_pass,"direct_record_binding":direct,"direct_record_pass":direct_pass,"structured_record_detail":structured,"structured_record_detail_pass":structured_pass,"expanded_record_detail":expanded,"expanded_goods_detail_pass":expanded_pass,"goods_relatedness_g0_g4":goods,"g0_g1_goods_pass":goods_pass,"pass":passed,"failure_signature":rec.get("failure_signature"),"observer_error":rec.get("post_terminal_observer_error")})
        browser.close()
    if len(output["canaries"])==2 and all(x["pass"] for x in output["canaries"]): output["phase_state"]="G0_G1_GOODS_RELATEDNESS_PASS"
    out=Path("artifacts/deep-interpretation"); out.mkdir(parents=True,exist_ok=True)
    (out/"receipt.json").write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")
    print("phase_state=",output["phase_state"])
    for x in output["canaries"]: print(x["candidate_key"],"goods=",(x.get("goods_relatedness_g0_g4") or {}).get("assessment"),"g0g1=",x["g0_g1_goods_pass"])
    if output["phase_state"]!="G0_G1_GOODS_RELATEDNESS_PASS": raise SystemExit("G0_G1_GOODS_RELATEDNESS_NOT_PASS")

if __name__=="__main__": main()
