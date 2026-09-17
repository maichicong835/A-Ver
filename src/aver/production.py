#!/usr/bin/env python3
import argparse, hashlib, json, os, re, subprocess
from pathlib import Path
import jsonschema
from playwright.sync_api import sync_playwright
from aver.decision import evaluate_tm_state
from aver.positive_recall import classify_expanded_partial_recall
from aver.query_plan import REQUIRED_DIMENSIONS, build_query_plan, normalize_wording
from aver.resolvers import TrademarkiaResolver
from aver.tsdr_targeted_canary import run_case as tsdr_case
from aver.uspto_fieldtag_direct_canary import run_case as usp_case

ENGINE_VERSION="0.1.0"
GRAMMAR=re.compile(r"^[A-Za-z0-9]+(?:[ -][A-Za-z0-9]+){1,2}[,.!?]?$",re.ASCII)
NONMATERIAL_PARTIAL="NONMATERIAL_DEAD_UNRELATED_EXPANDED_PARTIAL_RECALL"
NO_ACTIVE_CLASS016="NONMATERIAL_NO_ACTIVE_CLASS_016"
ACTIVE_CLASS016="ACTIVE_CLASS_016_POSITIVE_SCOPE"

def live_class016_query(q): return f"{q} AND LD:true AND IC:016"

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
 return {"query":q,"state":r.get("state"),"failure":r.get("failure_signature"),"count":t.get("count"),"polarity":pol,"single_record_detail":t.get("single_record_detail"),"final_url":t.get("final_url")}

def tm(resolver,s):
 q='"'+s.replace('"','').strip()+'"'; r=resolver.search(q,"OPAQUE_ZERO"); t=r.get("terminal_result") or {}; term=t.get("terminal")
 pol="NEGATIVE" if r.get("state")=="CAPABILITY_PASS" and term=="ZERO_RESULTSET" else "POSITIVE" if term=="POSITIVE_RESULTSET" else "UNRESOLVED"
 return {"query":q,"state":r.get("state"),"failure":r.get("failure_signature"),"terminal":term,"polarity":pol,"bound":bool((r.get("query_binding_attestation") or {}).get("bound"))}

def review_official_positive(browser,req,dimension,record,shared_component):
 detail=record.get("single_record_detail") or {}; serial=detail.get("serial_number"); mark=(detail.get("mark_text") or "").strip()
 if not serial or not mark: return {"classification":"MATERIALITY_UNRESOLVED","record_binding_complete":False,"reason":"USPTO_POSITIVE_RESULT_RECORD_DETAIL_NOT_BOUND","legal_clearance_asserted":False}
 tsdr=tsdr_case(browser,{"candidate_key":req.get("request_id","candidate"),"serial":serial,"mark":mark,"shared_component":shared_component or mark})
 review=classify_expanded_partial_recall(req,detail,tsdr.get("body_excerpt") or "",dimension)
 review["record_binding_complete"]=bool(review.get("record_binding_complete") and tsdr.get("state")=="PASS" and tsdr.get("serial_seen") is True and tsdr.get("mark_seen") is True)
 review["tsdr_state"]=tsdr.get("state"); review["tsdr_failure_signature"]=tsdr.get("failure_signature"); review["serial_number"]=serial; review["mark_text"]=mark
 return review

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
 rows=[]; dims={d:True for d in REQUIRED_DIMENSIONS}; positive_entries=[]; unresolved_transport=False; tm_qualified=all(grammar_ok(c) for c in cores)
 exe=os.getenv("AVER_BROWSER_EXECUTABLE") or None
 with sync_playwright() as p:
  launch={"headless":True}
  if exe: launch["executable_path"]=exe
  browser=p.chromium.launch(**launch); tr=TrademarkiaResolver(browser)
  def add(resolver,dim,rec,track_positive=True):
   nonlocal unresolved_transport
   rows.append((resolver,dim,rec)); unresolved_transport |= rec["polarity"]=="UNRESOLVED"
   if track_positive and rec["polarity"]=="POSITIVE": positive_entries.append((resolver,dim,rec))
  def resolve_official(dim,q,shared):
   r=usp(browser,q)
   add("USPTO_OFFICIAL_DIRECT_FIELDTAG",dim,r,track_positive=False)
   if r["polarity"]=="NEGATIVE": return True
   if r["polarity"]=="UNRESOLVED": return False
   # Operational Class-016 materiality rule:
   # a broad USPTO positive can block stickers only when the same scope has a LIVE IC:016 hit.
   # The narrower official filter must itself resolve; unresolved filter evidence fails closed.
   r16=usp(browser,live_class016_query(q))
   if r16["polarity"]=="NEGATIVE":
    add("USPTO_OFFICIAL_LIVE_IC016_FILTER",dim,r16,track_positive=False)
    r["positive_review"]={"classification":NO_ACTIVE_CLASS016,"record_binding_complete":True,"reason":"OFFICIAL_LIVE_IC016_FILTER_ZERO","federal_scope_only":True,"common_law_clearance_asserted":False,"legal_clearance_asserted":False}
    return True
   if r16["polarity"]=="UNRESOLVED":
    add("USPTO_OFFICIAL_LIVE_IC016_FILTER",dim,r16,track_positive=False)
    r["positive_review"]={"classification":"ACTIVE_CLASS_016_FILTER_UNRESOLVED","record_binding_complete":False,"reason":"OFFICIAL_LIVE_IC016_FILTER_UNRESOLVED","federal_scope_only":True,"common_law_clearance_asserted":False,"legal_clearance_asserted":False}
    return False
   review=review_official_positive(browser,req,dim,r16,shared)
   review["classification"]=ACTIVE_CLASS016
   review["active_class_016_query"]=r16["query"]
   r16["positive_review"]=review
   add("USPTO_OFFICIAL_LIVE_IC016_FILTER",dim,r16,track_positive=True)
   return False
  dims["EXACT"] &= resolve_official("EXACT",oq(wording),wording)
  norm=normalize_wording(wording); dims["NORMALIZED_EXACT"] &= resolve_official("NORMALIZED_EXACT",oq(norm),norm)
  for c in cores:
   dims["CORE_DOMINANT_TOKEN"] &= resolve_official("CORE_DOMINANT_TOKEN",oq(c),c)
   dims["EXPANDED_PARTIAL"] &= resolve_official("EXPANDED_PARTIAL",pq(c),c)
  for q in ph: dims["PHONETIC_OR_SPELLING_WHEN_MATERIAL"] &= resolve_official("PHONETIC_OR_SPELLING_WHEN_MATERIAL",q,"PHONETIC_OR_SPELLING")
  t=tm(tr,wording); add("TRADEMARKIA_QUOTED_LITERAL","EXACT",t); tm_qualified &= t["polarity"]=="NEGATIVE" and t["bound"]
  for c in cores:
   t=tm(tr,c); add("TRADEMARKIA_QUOTED_LITERAL","CORE_DOMINANT_TOKEN",t); tm_qualified &= t["polarity"]=="NEGATIVE" and t["bound"]
  browser.close()
 material_positive=[]; all_positive_bound=True; material_records=[]; nonmaterial_partial_count=0
 for resolver,dim,r in positive_entries:
  review=r.get("positive_review") or {}; bound=bool(review.get("record_binding_complete")); all_positive_bound &= bound
  if review.get("classification")==NONMATERIAL_PARTIAL and bound: nonmaterial_partial_count += 1
  else: material_positive.append((resolver,dim,r))
  detail=r.get("single_record_detail") or {}
  if detail.get("serial_number") and detail.get("mark_text"):
   status=(review.get("tsdr_status") or {}).get("state") or "POSITIVE_RECALL_STATUS_UNRESOLVED"
   if review.get("classification")==NONMATERIAL_PARTIAL: status="DEAD_INACTIVE_NONMATERIAL_EXPANDED_PARTIAL_RECALL"
   classes=",".join(detail.get("class_codes") or []) or "UNRESOLVED"; goods=(detail.get("goods_services_excerpt") or "UNRESOLVED").strip()
   material_records.append({"mark_text":detail["mark_text"][:300],"status":status[:120],"identifier":str(detail["serial_number"])[:120],"class_or_goods_services_context":f"classes={classes}; goods={goods}"[:1200]})
 material_positive_present=bool(material_positive)
 dims["RELATED_GOODS_REVIEW"]=all(dims[d] for d in REQUIRED_DIMENSIONS if d!="RELATED_GOODS_REVIEW") and not material_positive_present
 unresolved=[d for d,v in dims.items() if not v]
 if material_positive_present: unresolved += ["MATERIAL_RECORD_BINDING_AND_RELATEDNESS_REVIEW"]
 if not tm_qualified and not material_positive_present: unresolved += ["SECOND_SCOPE_QUALIFIED_NEGATIVE_SOURCE"]
 unresolved=list(dict.fromkeys(unresolved)); complete=all(dims.values()) and not material_positive_present
 qsources=2 if complete and tm_qualified else 1 if complete else 0
 decision=evaluate_tm_state({"material_positive_record_present":material_positive_present,"record_binding_complete":all_positive_bound if material_positive_present else True,"similarity_assessment":"CLEAR" if complete else "UNRESOLVED","goods_relatedness_assessment":"CLEAR" if complete else "UNRESOLVED","required_query_dimensions_complete":complete,"resolver_scope_complete":complete,"unresolved_dimensions":unresolved,"negative_evidence_distinct_sources":2,"scope_qualified_negative_evidence_distinct_sources":qsources,"transport_blocked":unresolved_transport,"control_blocked":False,"source_discordance":False})
 reason_codes=list(decision["decision_reason_codes"])
 if nonmaterial_partial_count: reason_codes.append("NONMATERIAL_DEAD_UNRELATED_EXPANDED_PARTIAL_RECALL_BOUND")
 no_active_class016_count=sum(1 for _resolver,_dim,_r in rows if ((_r.get("positive_review") or {}).get("classification")==NO_ACTIVE_CLASS016))
 if no_active_class016_count: reason_codes.append("NO_ACTIVE_CLASS_016_IN_POSITIVE_SCOPE")
 reason_codes=list(dict.fromkeys(reason_codes)); ev=[]; hashes=[]
 for resolver,dim,r in rows:
  h=jhash({"resolver":resolver,"dimension":dim,"record":r}); hashes.append(h); state=r.get("state") or r.get("terminal") or "OBSERVED"; review=r.get("positive_review") or {}
  if review.get("classification")==NONMATERIAL_PARTIAL: state="BOUND_NONMATERIAL_DEAD_UNRELATED_PARTIAL_RECALL"
  if review.get("classification")==NO_ACTIVE_CLASS016: state="FILTERED_NO_LIVE_CLASS_016"
  if review.get("classification")==ACTIVE_CLASS016: state="ACTIVE_CLASS_016_POSITIVE_SCOPE"
  ev.append({"resolver":resolver,"scope":f"{dim}:{r['query']}"[:240],"state":state[:120],"evidence_polarity":r["polarity"],"evidence_hash":h})
 out={"schema":"AVER_TM_RECEIPT","schema_version":"1.0","engine_version":ENGINE_VERSION,"engine_commit_sha":sha,"request_id":req["request_id"],"request_sha256":jhash(req),"decision":decision["decision"],"confidence_label":decision["confidence_label"],"legal_clearance_asserted":False,"decision_reason_codes":reason_codes,"query_plan":[{"dimension":d,"state":"RESOLVED" if dims[d] else "UNRESOLVED","resolver":"USPTO_OFFICIAL_DIRECT_FIELDTAG" if d!="RELATED_GOODS_REVIEW" else "A_VER_BOUND_RESULTSET_REVIEW"} for d in REQUIRED_DIMENSIONS],"resolver_evidence":ev,"material_records":material_records,"unresolved_dimensions":unresolved,"scope_coverage":{"required_query_dimensions_complete":complete,"resolver_scope_complete":complete,"negative_evidence_distinct_sources":2,"scope_qualified_negative_evidence_distinct_sources":qsources},"similarity_analysis":"CLEAR" if complete else "UNRESOLVED","goods_relatedness":"CLEAR" if complete else "UNRESOLVED","evidence_hashes":list(dict.fromkeys(hashes))}
 jsonschema.Draft202012Validator(oschema).validate(out); return out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--request",required=True); ap.add_argument("--output",required=True); ap.add_argument("--request-schema",default="spec/request.schema.json"); ap.add_argument("--receipt-schema",default="spec/receipt.schema.json"); a=ap.parse_args()
 req=json.loads(Path(a.request).read_text()); out=evaluate(req,json.loads(Path(a.request_schema).read_text()),json.loads(Path(a.receipt_schema).read_text())); p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2)+"\n"); print(out["decision"],out["decision_reason_codes"],out["unresolved_dimensions"])
if __name__=="__main__": main()
