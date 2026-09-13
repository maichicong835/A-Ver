#!/usr/bin/env python3
import argparse, hashlib, json, os, re, subprocess
from pathlib import Path
import jsonschema
from playwright.sync_api import sync_playwright
from aver.decision import evaluate_tm_state
from aver.query_plan import REQUIRED_DIMENSIONS, build_query_plan, normalize_wording
from aver.resolvers import TrademarkiaResolver
from aver.uspto_fieldtag_direct_canary import run_case as usp_case

ENGINE_VERSION="0.1.0"
GRAMMAR=re.compile(r"^[A-Za-z0-9]+(?:[ -][A-Za-z0-9]+){1,2}[,.!?]?$",re.ASCII)

def jhash(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def head():
 v=(os.getenv("AVER_ENGINE_COMMIT_SHA") or "").strip().lower()
 if re.fullmatch(r"[0-9a-f]{40}",v): return v
 return subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
def oq(s): return 'CM:"'+s.replace('"','').strip()+'"'
def pq(s): return "CM:("+" AND ".join(f"/.*{re.escape(x)}.*/" for x in re.findall(r"[a-z0-9]+",s.lower()))+")"
def grammar_ok(s): return bool(GRAMMAR.fullmatch(s.strip()))

def usp(browser,q):
 r=usp_case(browser,{"name":q,"query":q,"expected":"ZERO"}); t=r.get("terminal") or {}
 if r.get("state")=="PASS" and t.get("native_zero") is True: pol="NEGATIVE"
 elif t.get("positive") is True: pol="POSITIVE"
 else: pol="UNRESOLVED"
 return {"query":q,"state":r.get("state"),"failure":r.get("failure_signature"),"count":t.get("count"),"polarity":pol}

def tm(resolver,s):
 q='"'+s.replace('"','').strip()+'"'; r=resolver.search(q,"OPAQUE_ZERO"); t=r.get("terminal_result") or {}; term=t.get("terminal")
 pol="NEGATIVE" if r.get("state")=="CAPABILITY_PASS" and term=="ZERO_RESULTSET" else "POSITIVE" if term=="POSITIVE_RESULTSET" else "UNRESOLVED"
 return {"query":q,"state":r.get("state"),"failure":r.get("failure_signature"),"terminal":term,"polarity":pol,"bound":bool((r.get("query_binding_attestation") or {}).get("bound"))}

def hold(req,sha,reasons,unresolved):
 return {"schema":"AVER_TM_RECEIPT","schema_version":"1.0","engine_version":ENGINE_VERSION,"engine_commit_sha":sha,"request_id":req.get("request_id","invalid"),"request_sha256":jhash(req),"decision":"TM_HOLD","confidence_label":"EVIDENCE_INCOMPLETE","legal_clearance_asserted":False,"decision_reason_codes":reasons,"query_plan":[{"dimension":d,"state":"UNRESOLVED","resolver":"NONE"} for d in REQUIRED_DIMENSIONS],"resolver_evidence":[],"material_records":[],"unresolved_dimensions":unresolved,"scope_coverage":{"required_query_dimensions_complete":False,"resolver_scope_complete":False,"negative_evidence_distinct_sources":0,"scope_qualified_negative_evidence_distinct_sources":0},"similarity_analysis":"UNRESOLVED","goods_relatedness":"UNRESOLVED","evidence_hashes":[]}

def evaluate(req,rschema,oschema):
 sha=head()
 try: jsonschema.Draft202012Validator(rschema).validate(req)
 except Exception:
  out=hold(req,sha,["REQUEST_SCHEMA_INVALID"],REQUIRED_DIMENSIONS); jsonschema.Draft202012Validator(oschema).validate(out); return out
 missing=[d for d in REQUIRED_DIMENSIONS if d not in req["requested_scope"]["query_dimensions"]]
 if missing:
  out=hold(req,sha,["REQUEST_SCOPE_MISSING_REQUIRED_DIMENSIONS"],missing); jsonschema.Draft202012Validator(oschema).validate(out); return out
 wording=req["wording"].strip(); plan=build_query_plan(wording,[]); cores=plan["CORE_DOMINANT_TOKEN"]["queries"]; ph=plan["PHONETIC_OR_SPELLING_WHEN_MATERIAL"].get("queries") or []
 if not cores or not ph:
  out=hold(req,sha,["QUERY_PLAN_INCOMPLETE"],["CORE_DOMINANT_TOKEN","PHONETIC_OR_SPELLING_WHEN_MATERIAL"]); jsonschema.Draft202012Validator(oschema).validate(out); return out
 rows=[]; dims={d:True for d in REQUIRED_DIMENSIONS}; positive=False; unresolved_transport=False; tm_qualified=grammar_ok(wording) and all(grammar_ok(c) for c in cores)
 exe=os.getenv("AVER_BROWSER_EXECUTABLE") or None
 with sync_playwright() as p:
  launch={"headless":True}
  if exe: launch["executable_path"]=exe
  browser=p.chromium.launch(**launch); tr=TrademarkiaResolver(browser)
  def add(resolver,dim,rec):
   nonlocal positive,unresolved_transport
   rows.append((resolver,dim,rec)); positive |= rec["polarity"]=="POSITIVE"; unresolved_transport |= rec["polarity"]=="UNRESOLVED"
  r=usp(browser,oq(wording)); add("USPTO_OFFICIAL_DIRECT_FIELDTAG","EXACT",r); dims["EXACT"] &= r["polarity"]=="NEGATIVE"
  norm=normalize_wording(wording); r=usp(browser,oq(norm)); add("USPTO_OFFICIAL_DIRECT_FIELDTAG","NORMALIZED_EXACT",r); dims["NORMALIZED_EXACT"] &= r["polarity"]=="NEGATIVE"
  for c in cores:
   r=usp(browser,oq(c)); add("USPTO_OFFICIAL_DIRECT_FIELDTAG","CORE_DOMINANT_TOKEN",r); dims["CORE_DOMINANT_TOKEN"] &= r["polarity"]=="NEGATIVE"
   r=usp(browser,pq(c)); add("USPTO_OFFICIAL_DIRECT_FIELDTAG","EXPANDED_PARTIAL",r); dims["EXPANDED_PARTIAL"] &= r["polarity"]=="NEGATIVE"
  for q in ph:
   r=usp(browser,q); add("USPTO_OFFICIAL_DIRECT_FIELDTAG","PHONETIC_OR_SPELLING_WHEN_MATERIAL",r); dims["PHONETIC_OR_SPELLING_WHEN_MATERIAL"] &= r["polarity"]=="NEGATIVE"
  t=tm(tr,wording); add("TRADEMARKIA_QUOTED_LITERAL","EXACT",t); tm_qualified &= t["polarity"]=="NEGATIVE" and t["bound"]
  for c in cores:
   t=tm(tr,c); add("TRADEMARKIA_QUOTED_LITERAL","CORE_DOMINANT_TOKEN",t); tm_qualified &= t["polarity"]=="NEGATIVE" and t["bound"]
  browser.close()
 dims["RELATED_GOODS_REVIEW"]=all(dims[d] for d in REQUIRED_DIMENSIONS if d!="RELATED_GOODS_REVIEW") and not positive
 unresolved=[d for d,v in dims.items() if not v]
 if positive: unresolved += ["MATERIAL_RECORD_BINDING_AND_RELATEDNESS_REVIEW"]
 if not tm_qualified and not positive: unresolved += ["SECOND_SCOPE_QUALIFIED_NEGATIVE_SOURCE"]
 unresolved=list(dict.fromkeys(unresolved)); complete=all(dims.values()) and not positive
 qsources=2 if complete and tm_qualified else 1 if complete else 0
 decision=evaluate_tm_state({"material_positive_record_present":positive,"record_binding_complete":False if positive else True,"similarity_assessment":"CLEAR" if complete else "UNRESOLVED","goods_relatedness_assessment":"CLEAR" if complete else "UNRESOLVED","required_query_dimensions_complete":complete,"resolver_scope_complete":complete,"unresolved_dimensions":unresolved,"negative_evidence_distinct_sources":2,"scope_qualified_negative_evidence_distinct_sources":qsources,"transport_blocked":unresolved_transport,"control_blocked":False,"source_discordance":False})
 ev=[]; hashes=[]
 for resolver,dim,r in rows:
  h=jhash({"resolver":resolver,"dimension":dim,"record":r}); hashes.append(h); ev.append({"resolver":resolver,"scope":f"{dim}:{r['query']}"[:240],"state":r.get("state") or r.get("terminal") or "OBSERVED","evidence_polarity":r["polarity"],"evidence_hash":h})
 out={"schema":"AVER_TM_RECEIPT","schema_version":"1.0","engine_version":ENGINE_VERSION,"engine_commit_sha":sha,"request_id":req["request_id"],"request_sha256":jhash(req),"decision":decision["decision"],"confidence_label":decision["confidence_label"],"legal_clearance_asserted":False,"decision_reason_codes":decision["decision_reason_codes"],"query_plan":[{"dimension":d,"state":"RESOLVED" if dims[d] else "UNRESOLVED","resolver":"USPTO_OFFICIAL_DIRECT_FIELDTAG" if d!="RELATED_GOODS_REVIEW" else "A_VER_BOUND_RESULTSET_REVIEW"} for d in REQUIRED_DIMENSIONS],"resolver_evidence":ev,"material_records":[],"unresolved_dimensions":unresolved,"scope_coverage":{"required_query_dimensions_complete":complete,"resolver_scope_complete":complete,"negative_evidence_distinct_sources":2,"scope_qualified_negative_evidence_distinct_sources":qsources},"similarity_analysis":"CLEAR" if complete else "UNRESOLVED","goods_relatedness":"CLEAR" if complete else "UNRESOLVED","evidence_hashes":list(dict.fromkeys(hashes))}
 jsonschema.Draft202012Validator(oschema).validate(out); return out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--request",required=True); ap.add_argument("--output",required=True); ap.add_argument("--request-schema",default="spec/request.schema.json"); ap.add_argument("--receipt-schema",default="spec/receipt.schema.json"); a=ap.parse_args()
 req=json.loads(Path(a.request).read_text()); out=evaluate(req,json.loads(Path(a.request_schema).read_text()),json.loads(Path(a.receipt_schema).read_text())); p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2)+"\n"); print(out["decision"],out["unresolved_dimensions"])
if __name__=="__main__": main()
