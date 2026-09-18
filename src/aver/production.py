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
NONMATERIAL_WEAK_CORE="NONMATERIAL_CROWDED_LOW_CONTEXT_CORE_CLASS_016"
CORE_STOPWORDS={"a","an","and","are","as","at","be","by","for","from","i","in","is","it","of","on","or","the","to","we","with","you","your"}
STICKER_RELATED_GOODS_ANCHORS={"sticker","stickers","decal","decals","label","labels","adhesive","bumper"}

def _content_tokens(value):
 return [t for t in re.findall(r"[a-z0-9]+",(value or "").lower()) if len(t)>1 and t not in CORE_STOPWORDS]

def _weak_core_context_tokens(wording,core,limit=2):
 core_set=set(_content_tokens(core)); out=[]; seen=set()
 for i,t in enumerate(_content_tokens(wording)):
  if t in core_set or t in seen: continue
  seen.add(t); out.append((len(t),i,t))
 out.sort(key=lambda x:(-x[0],x[1],x[2]))
 return [t for _,_,t in out[:limit]]

def _weak_core_shape(wording,core,record_mark):
 cand=_content_tokens(wording); rec=_content_tokens(record_mark); shared=set(cand)&set(rec); core_set=set(_content_tokens(core))
 return {
  "candidate_content_tokens":cand,
  "record_content_tokens":rec,
  "core_content_tokens":sorted(core_set),
  "shared_outside_core":sorted(shared-core_set),
  "candidate_overlap_ratio":round(len(shared)/max(1,len(set(cand))),4),
  "record_overlap_ratio":round(len(shared)/max(1,len(set(rec))),4),
 }

def _direct_sticker_goods_overlap(req,detail):
 intended=set(_content_tokens(((req.get("intended_goods_context") or {}).get("description") or "")))
 record=set(_content_tokens((detail or {}).get("goods_services_excerpt") or ""))
 return bool({"sticker","stickers","decal","decals"} & intended) and bool(STICKER_RELATED_GOODS_ANCHORS & record)


def live_class016_query(q): return f"{q} AND LD:true AND IC:016"
def _core_crowding_query(core): return oq(core)+" AND LD:true"
def _core_context_query(core,token): return oq(core)+f" AND CM:{token.upper()} AND LD:true AND IC:016"
COMMON_LOW_SIGNAL={"this","that","with","from","your","have","will","just","into","work","here","last","time","can"}
COMPONENT_GUARD_MAX_TOKEN_LENGTH=4
def distinctive_tokens(value):
 toks=re.findall(r"[a-z0-9]+",(value or "").lower())
 ranked=[(i,t) for i,t in enumerate(toks) if len(t)>=4 and t not in COMMON_LOW_SIGNAL]
 ranked=sorted(ranked,key=lambda x:(-len(x[1]),x[0]))
 out=[]
 for _,t in ranked:
  if t not in out: out.append(t)
 return out
def distinctive_live_class016_query(value):
 toks=distinctive_tokens(value)[:2]
 if len(toks)<2: return None
 return "CM:("+ " AND ".join(f"/.*{re.escape(t)}.*/" for t in toks) + ") AND LD:true AND IC:016"

def _independent_component_candidates(wording,nonmaterial_cores,limit=3):
 core_tokens=set()
 for core in nonmaterial_cores:
  core_tokens.update(_content_tokens(core))
 out=[]
 for i,t in enumerate(_content_tokens(wording)):
  if t in core_tokens or t in COMMON_LOW_SIGNAL or len(t)>COMPONENT_GUARD_MAX_TOKEN_LENGTH:
   continue
  if t not in [x[2] for x in out]:
   out.append((len(t),i,t))
 out.sort(key=lambda x:(x[0],x[1],x[2]))
 return [t for _,_,t in out[:limit]]

def _body_has_exact_live_wordmark(record,token):
 body=(record or {}).get("body_excerpt") or ""
 return bool(re.search(r"\\bWordmark\\s+wordmark\\s+"+re.escape(token)+r"\\s+Status\\s+LIVE",body,re.I))

def jhash(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def head():
 v=(os.getenv("AVER_ENGINE_COMMIT_SHA") or "").strip().lower()
 if re.fullmatch(r"[0-9a-f]{40}",v): return v
 return subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
def oq(s): return 'CM:"'+s.replace('"','').strip()+'"'
def pq(s):
 toks=re.findall(r"[a-z0-9]+",s.lower()); long=[x for x in toks if len(x)>3]; short=[x for x in toks if len(x)<=3]; parts=[]
 if long: parts.append("CM:("+ " AND ".join(f"/.*{re.escape(x)}.*/" for x in long)+")")
 parts.extend(f"CM:{x.upper()}" for x in short)
 return " AND ".join(parts)
def grammar_ok(s): return bool(GRAMMAR.fullmatch(s.strip()))

def usp(browser,q):
 r=usp_case(browser,{"name":q,"query":q,"expected":"ZERO"}); t=r.get("terminal") or {}
 if r.get("state")=="PASS" and t.get("native_zero") is True: pol="NEGATIVE"
 elif t.get("positive") is True: pol="POSITIVE"
 else: pol="UNRESOLVED"
 return {"query":q,"state":r.get("state"),"failure":r.get("failure_signature"),"count":t.get("count"),"polarity":pol,"single_record_detail":t.get("single_record_detail"),"final_url":t.get("final_url"),"body_excerpt":t.get("body_excerpt")}

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
 rows=[]; dims={d:True for d in REQUIRED_DIMENSIONS}; positive_entries=[]; nonmaterial_cores=set(); unresolved_transport=False; tm_qualified=all(grammar_ok(c) for c in cores)
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
   if r["polarity"]=="NEGATIVE":
    add("USPTO_OFFICIAL_DIRECT_FIELDTAG",dim,r,track_positive=False)
    return True
   if r["polarity"]=="UNRESOLVED":
    add("USPTO_OFFICIAL_DIRECT_FIELDTAG",dim,r,track_positive=False)
    return False
   # Whole-wording positives cannot be dismissed solely because the record is outside IC 016.
   if dim in ("EXACT","NORMALIZED_EXACT"):
    review=review_official_positive(browser,req,dim,r,shared)
    r["positive_review"]=review
    add("USPTO_OFFICIAL_DIRECT_FIELDTAG",dim,r,track_positive=True)
    return False
   add("USPTO_OFFICIAL_DIRECT_FIELDTAG",dim,r,track_positive=False)
   r16=usp(browser,live_class016_query(q))
   if r16["polarity"]=="NEGATIVE":
    add("USPTO_OFFICIAL_LIVE_IC016_FILTER",dim,r16,track_positive=False)
    r["positive_review"]={"classification":NO_ACTIVE_CLASS016,"record_binding_complete":True,"reason":"OFFICIAL_LIVE_IC016_FILTER_ZERO","federal_scope_only":True,"common_law_clearance_asserted":False,"legal_clearance_asserted":False}
    return True
   if r16["polarity"]=="UNRESOLVED":
    add("USPTO_OFFICIAL_LIVE_IC016_FILTER",dim,r16,track_positive=False)
    r["positive_review"]={"classification":"ACTIVE_CLASS_016_FILTER_UNRESOLVED","record_binding_complete":False,"reason":"OFFICIAL_LIVE_IC016_FILTER_UNRESOLVED","federal_scope_only":True,"common_law_clearance_asserted":False,"legal_clearance_asserted":False}
    return False
   if dim=="EXPANDED_PARTIAL":
    dq=distinctive_live_class016_query(wording)
    if dq:
     rd=usp(browser,dq)
     add("USPTO_OFFICIAL_DISTINCTIVE_LIVE_IC016_FILTER",dim,rd,track_positive=False)
     if rd["polarity"]=="NEGATIVE":
      r["positive_review"]={"classification":"NONMATERIAL_EXPANDED_PARTIAL_NO_DISTINCTIVE_LIVE_CLASS_016","record_binding_complete":True,"reason":"DISTINCTIVE_CANDIDATE_LIVE_IC016_FILTER_ZERO","federal_scope_only":True,"common_law_clearance_asserted":False,"legal_clearance_asserted":False}
      return True
     if rd["polarity"]=="UNRESOLVED":
      return False
   review=review_official_positive(browser,req,dim,r16,shared)
   if dim=="CORE_DOMINANT_TOKEN" and review.get("record_binding_complete") and ((review.get("tsdr_status") or {}).get("state")=="LIVE_ACTIVE"):
    detail=r16.get("single_record_detail") or {}
    shape=_weak_core_shape(wording,shared,detail.get("mark_text") or "")
    crowd=usp(browser,_core_crowding_query(shared))
    add("USPTO_OFFICIAL_CORE_CROWDING",dim,crowd,track_positive=False)
    ctx_tokens=_weak_core_context_tokens(wording,shared,limit=2); ctx=[]
    for tok in ctx_tokens:
     cr=usp(browser,_core_context_query(shared,tok))
     add("USPTO_OFFICIAL_CORE_CONTEXT",dim,cr,track_positive=False)
     ctx.append((tok,cr))
    weak_core_ok=bool(
      dims["EXACT"] and dims["NORMALIZED_EXACT"]
      and len(shape["core_content_tokens"])<=3
      and len(set(shape["candidate_content_tokens"]))>=5
      and len(set(shape["record_content_tokens"]))>=4
      and not shape["shared_outside_core"]
      and shape["candidate_overlap_ratio"]<=0.40
      and shape["record_overlap_ratio"]<=0.50
      and crowd["polarity"]=="POSITIVE" and int(crowd.get("count") or 0)>=3
      and len(ctx)>=2 and all(x[1]["polarity"]=="NEGATIVE" for x in ctx)
      and not _direct_sticker_goods_overlap(req,detail)
    )
    if weak_core_ok:
     review.update({
      "classification":NONMATERIAL_WEAK_CORE,
      "reason":"CROWDED_LOW_CONTEXT_CORE_WITHOUT_CANDIDATE_REINFORCEMENT_OR_DIRECT_STICKER_GOODS",
      "core_crowding_live_count":int(crowd.get("count") or 0),
      "context_reinforcement_tokens":[x[0] for x in ctx],
      "context_reinforcement_all_live_ic016_zero":True,
      "whole_mark_shape":shape,
      "direct_sticker_goods_overlap":False,
      "federal_scope_only":True,
      "common_law_clearance_asserted":False,
      "legal_clearance_asserted":False,
     })
     r16["positive_review"]=review
     add("USPTO_OFFICIAL_LIVE_IC016_FILTER",dim,r16,track_positive=False)
     nonmaterial_cores.add(normalize_wording(shared))
     return True
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
  component_hold_tokens=[]
  if nonmaterial_cores:
   for tok in _independent_component_candidates(wording,nonmaterial_cores,limit=3):
    cr=usp(browser,f"CM:{tok.upper()} AND LD:true AND IC:016")
    if cr["polarity"]=="POSITIVE" and _body_has_exact_live_wordmark(cr,tok):
     cr["positive_review"]={"classification":"ACTIVE_CLASS_016_COMPONENT_WORDMARK","record_binding_complete":False,"reason":"EXACT_COMPONENT_WORDMARK_LIVE_IN_CLASS_016_REQUIRES_BOUNDED_REVIEW","federal_scope_only":True,"common_law_clearance_asserted":False,"legal_clearance_asserted":False}
     component_hold_tokens.append(tok.upper())
     dims["CORE_DOMINANT_TOKEN"]=False
    elif cr["polarity"]=="UNRESOLVED":
     component_hold_tokens.append(tok.upper())
     dims["CORE_DOMINANT_TOKEN"]=False
    add("USPTO_OFFICIAL_COMPONENT_CLASS016","CORE_DOMINANT_TOKEN",cr,track_positive=False)
  t=tm(tr,wording); add("TRADEMARKIA_QUOTED_LITERAL","EXACT",t); tm_qualified &= t["polarity"]=="NEGATIVE" and t["bound"]
  for c in cores:
   t=tm(tr,c); key=normalize_wording(c)
   if t["polarity"]=="POSITIVE" and key in nonmaterial_cores and t["bound"]:
    t["positive_review"]={"classification":"CORROBORATED_NONMATERIAL_WEAK_CORE","official_materiality_authority":"USPTO","legal_clearance_asserted":False}
    add("TRADEMARKIA_QUOTED_LITERAL","CORE_DOMINANT_TOKEN",t,track_positive=False)
    tm_qualified &= True
   else:
    add("TRADEMARKIA_QUOTED_LITERAL","CORE_DOMINANT_TOKEN",t)
    tm_qualified &= t["polarity"]=="NEGATIVE" and t["bound"]
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
 if component_hold_tokens: unresolved += ["ACTIVE_CLASS016_COMPONENT_WORDMARK_REVIEW"]
 if not tm_qualified and not material_positive_present: unresolved += ["SECOND_SCOPE_QUALIFIED_NEGATIVE_SOURCE"]
 unresolved=list(dict.fromkeys(unresolved)); complete=all(dims.values()) and not material_positive_present
 qsources=2 if complete and tm_qualified else 1 if complete else 0
 decision=evaluate_tm_state({"material_positive_record_present":material_positive_present,"record_binding_complete":all_positive_bound if material_positive_present else True,"similarity_assessment":"CLEAR" if complete else "UNRESOLVED","goods_relatedness_assessment":"CLEAR" if complete else "UNRESOLVED","required_query_dimensions_complete":complete,"resolver_scope_complete":complete,"unresolved_dimensions":unresolved,"negative_evidence_distinct_sources":2,"scope_qualified_negative_evidence_distinct_sources":qsources,"transport_blocked":unresolved_transport,"control_blocked":False,"source_discordance":False})
 reason_codes=list(decision["decision_reason_codes"])
 if nonmaterial_partial_count: reason_codes.append("NONMATERIAL_DEAD_UNRELATED_EXPANDED_PARTIAL_RECALL_BOUND")
 no_active_class016_count=sum(1 for _resolver,_dim,_r in rows if ((_r.get("positive_review") or {}).get("classification")==NO_ACTIVE_CLASS016))
 if no_active_class016_count: reason_codes.append("NO_ACTIVE_CLASS_016_IN_POSITIVE_SCOPE")
 nonmaterial_distinctive_count=sum(1 for _resolver,_dim,_r in rows if ((_r.get("positive_review") or {}).get("classification")=="NONMATERIAL_EXPANDED_PARTIAL_NO_DISTINCTIVE_LIVE_CLASS_016"))
 if nonmaterial_distinctive_count: reason_codes.append("NO_DISTINCTIVE_LIVE_CLASS_016_IN_EXPANDED_SCOPE")
 weak_core_count=sum(1 for _resolver,_dim,_r in rows if ((_r.get("positive_review") or {}).get("classification")==NONMATERIAL_WEAK_CORE))
 if weak_core_count: reason_codes.append("NONMATERIAL_CROWDED_LOW_CONTEXT_CORE_CLASS_016_BOUND")
 if component_hold_tokens: reason_codes.append("ACTIVE_CLASS_016_COMPONENT_WORDMARK_REQUIRES_BOUNDED_REVIEW")
 reason_codes=list(dict.fromkeys(reason_codes)); ev=[]; hashes=[]
 for resolver,dim,r in rows:
  h=jhash({"resolver":resolver,"dimension":dim,"record":r}); hashes.append(h); state=r.get("state") or r.get("terminal") or "OBSERVED"; review=r.get("positive_review") or {}
  if review.get("classification")==NONMATERIAL_PARTIAL: state="BOUND_NONMATERIAL_DEAD_UNRELATED_PARTIAL_RECALL"
  if review.get("classification")==NO_ACTIVE_CLASS016: state="FILTERED_NO_LIVE_CLASS_016"
  if review.get("classification")=="NONMATERIAL_EXPANDED_PARTIAL_NO_DISTINCTIVE_LIVE_CLASS_016": state="FILTERED_NO_DISTINCTIVE_LIVE_CLASS_016"
  if review.get("classification")==NONMATERIAL_WEAK_CORE: state="BOUND_NONMATERIAL_CROWDED_LOW_CONTEXT_CORE_CLASS_016"
  if review.get("classification")=="CORROBORATED_NONMATERIAL_WEAK_CORE": state="CORROBORATED_NONMATERIAL_WEAK_CORE"
  if review.get("classification")=="ACTIVE_CLASS_016_COMPONENT_WORDMARK": state="ACTIVE_CLASS_016_COMPONENT_WORDMARK"
  if review.get("classification")==ACTIVE_CLASS016: state="ACTIVE_CLASS_016_POSITIVE_SCOPE"
  ev.append({"resolver":resolver,"scope":f"{dim}:{r['query']}"[:240],"state":state[:120],"evidence_polarity":r["polarity"],"evidence_hash":h})
 out={"schema":"AVER_TM_RECEIPT","schema_version":"1.0","engine_version":ENGINE_VERSION,"engine_commit_sha":sha,"request_id":req["request_id"],"request_sha256":jhash(req),"decision":decision["decision"],"confidence_label":decision["confidence_label"],"legal_clearance_asserted":False,"decision_reason_codes":reason_codes,"query_plan":[{"dimension":d,"state":"RESOLVED" if dims[d] else "UNRESOLVED","resolver":"USPTO_OFFICIAL_DIRECT_FIELDTAG" if d!="RELATED_GOODS_REVIEW" else "A_VER_BOUND_RESULTSET_REVIEW"} for d in REQUIRED_DIMENSIONS],"resolver_evidence":ev,"material_records":material_records,"unresolved_dimensions":unresolved,"scope_coverage":{"required_query_dimensions_complete":complete,"resolver_scope_complete":complete,"negative_evidence_distinct_sources":2,"scope_qualified_negative_evidence_distinct_sources":qsources},"similarity_analysis":"CLEAR" if complete else "UNRESOLVED","goods_relatedness":"CLEAR" if complete else "UNRESOLVED","evidence_hashes":list(dict.fromkeys(hashes))}
 jsonschema.Draft202012Validator(oschema).validate(out); return out

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--request",required=True); ap.add_argument("--output",required=True); ap.add_argument("--request-schema",default="spec/request.schema.json"); ap.add_argument("--receipt-schema",default="spec/receipt.schema.json"); a=ap.parse_args()
 req=json.loads(Path(a.request).read_text()); out=evaluate(req,json.loads(Path(a.request_schema).read_text()),json.loads(Path(a.receipt_schema).read_text())); p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2)+"\n"); print(out["decision"],out["decision_reason_codes"],out["unresolved_dimensions"])
if __name__=="__main__": main()
