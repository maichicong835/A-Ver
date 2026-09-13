#!/usr/bin/env python3
import json, os
from pathlib import Path
from playwright.sync_api import sync_playwright
from aver.resolvers import TrademarkiaResolver

CASES=[
 {"name":"POSITIVE","query":"\"JUST DO IT\"","expected":"KNOWN_POSITIVE","identifier":"50086105","want":"POSITIVE_RESULTSET"},
 {"name":"ZERO_2_TOKEN","query":"\"QZXJVMRKPLNX VQTKRMNZXJQW\"","expected":"OPAQUE_ZERO","identifier":None,"want":"ZERO_RESULTSET"},
 {"name":"ZERO_3_TOKEN","query":"\"PLQZXM VTRKQJ NXMWZA\"","expected":"OPAQUE_ZERO","identifier":None,"want":"ZERO_RESULTSET"},
 {"name":"ZERO_PUNCTUATED","query":"\"QZXJ-VMRK, PLNXQ\"","expected":"OPAQUE_ZERO","identifier":None,"want":"ZERO_RESULTSET"}
]

def main():
 out={"schema":"AVER_TRADEMARKIA_QUOTED_GRAMMAR_CANARY","schema_version":"1.0","scope":"QUOTED_LITERAL_MULTIWORD_2_TO_3_TOKEN_ASCII_WITH_OPTIONAL_BASIC_PUNCTUATION","fixed_non_daily7_canaries":True,"daily7_candidate_queries_executed":False,"generalization_beyond_declared_grammar_forbidden":True,"phase_state":"PARTIAL","cases":[]}
 exe=os.getenv("AVER_BROWSER_EXECUTABLE") or None
 with sync_playwright() as p:
  launch={"headless":True}
  if exe: launch["executable_path"]=exe
  browser=p.chromium.launch(**launch); r=TrademarkiaResolver(browser)
  for c in CASES:
   rec=r.search(c["query"],c["expected"],expected_identifier=c["identifier"])
   term=(rec.get("terminal_result") or {}).get("terminal")
   bound=(rec.get("query_binding_attestation") or {}).get("bound") is True
   out["cases"].append({"name":c["name"],"query":c["query"],"state":rec.get("state"),"terminal":term,"bound":bound,"pass":rec.get("state")=="CAPABILITY_PASS" and term==c["want"] and bound,"failure_signature":rec.get("failure_signature")})
  browser.close()
 if all(x["pass"] for x in out["cases"]): out["phase_state"]="QUOTED_MULTIWORD_GRAMMAR_CANARY_PASS"
 path=Path("artifacts/trademarkia-quoted-grammar"); path.mkdir(parents=True,exist_ok=True); (path/"receipt.json").write_text(json.dumps(out,indent=2)+"\n")
 print("phase_state=",out["phase_state"])
 for x in out["cases"]: print(x["name"],x["state"],x["terminal"],x["bound"],x["failure_signature"])
 if out["phase_state"]!="QUOTED_MULTIWORD_GRAMMAR_CANARY_PASS": raise SystemExit("QUOTED_GRAMMAR_NOT_PROVEN")
if __name__=="__main__": main()
