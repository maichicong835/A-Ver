#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import subprocess
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


def jhash(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()


def head():
    value=(os.getenv("AVER_ENGINE_COMMIT_SHA") or "").strip().lower()
    if re.fullmatch(r"[0-9a-f]{40}",value):
        return value
    return subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()


def oq(value):
    return 'CM:"'+value.replace('"','').strip()+'"'


def pq(value):
    return "CM:("+" AND ".join(f"/.*{re.escape(x)}.*/" for x in re.findall(r"[a-z0-9]+",value.lower()))+")"


def grammar_ok(value):
    return bool(GRAMMAR.fullmatch(value.strip()))


def usp(browser,query):
    raw=usp_case(browser,{"name":query,"query":query,"expected":"ZERO"})
    terminal=raw.get("terminal") or {}
    if raw.get("state")=="PASS" and terminal.get("native_zero") is True:
        polarity="NEGATIVE"
        state="CAPABILITY_PASS_NATIVE_ZERO"
        failure=None
    elif terminal.get("positive") is True:
        polarity="POSITIVE"
        state="CAPABILITY_PASS_POSITIVE_RESULTSET"
        failure=None
    else:
        polarity="UNRESOLVED"
        state=raw.get("state") or "UNPROVEN"
        failure=raw.get("failure_signature")
    return {
        "query":query,
        "state":state,
        "failure":failure,
        "count":terminal.get("count"),
        "polarity":polarity,
        "single_record_detail":terminal.get("single_record_detail"),
        "final_url":terminal.get("final_url"),
    }


def tm(resolver,value):
    query='"'+value.replace('"','').strip()+'"'
    raw=resolver.search(query,"OPAQUE_ZERO")
    terminal=raw.get("terminal_result") or {}
    term=terminal.get("terminal")
    if raw.get("state")=="CAPABILITY_PASS" and term=="ZERO_RESULTSET":
        polarity="NEGATIVE"
    elif term=="POSITIVE_RESULTSET":
        polarity="POSITIVE"
    else:
        polarity="UNRESOLVED"
    return {
        "query":query,
        "state":raw.get("state"),
        "failure":raw.get("failure_signature"),
        "terminal":term,
        "polarity":polarity,
        "bound":bool((raw.get("query_binding_attestation") or {}).get("bound")),
    }


def review_official_positive(browser,request,dimension,record,shared_component):
    detail=record.get("single_record_detail") or {}
    serial=detail.get("serial_number")
    mark=(detail.get("mark_text") or "").strip()
    if not serial or not mark:
        return {
            "classification":"MATERIALITY_UNRESOLVED",
            "record_binding_complete":False,
            "reason":"USPTO_POSITIVE_RESULT_RECORD_DETAIL_NOT_BOUND",
            "legal_clearance_asserted":False,
        }
    tsdr=tsdr_case(browser,{
        "candidate_key":request.get("request_id","candidate"),
        "serial":serial,
        "mark":mark,
        "shared_component":shared_component or mark,
    })
    body=tsdr.get("body_excerpt") or ""
    classification=classify_expanded_partial_recall(request,detail,body,dimension)
    classification["record_binding_complete"]=bool(
        classification.get("record_binding_complete")
        and tsdr.get("state")=="PASS"
        and tsdr.get("serial_seen") is True
        and tsdr.get("mark_seen") is True
    )
    classification["tsdr_state"]=tsdr.get("state")
    classification["tsdr_failure_signature"]=tsdr.get("failure_signature")
    classification["tsdr_retry_count"]=tsdr.get("retry_count")
    classification["serial_number"]=serial
    classification["mark_text"]=mark
    return classification


def hold(request,sha,reasons,unresolved):
    return {
        "schema":"AVER_TM_RECEIPT",
        "schema_version":"1.0",
        "engine_version":ENGINE_VERSION,
        "engine_commit_sha":sha,
        "request_id":request.get("request_id","invalid"),
        "request_sha256":jhash(request),
        "decision":"TM_HOLD",
        "confidence_label":"EVIDENCE_INCOMPLETE",
        "legal_clearance_asserted":False,
        "decision_reason_codes":reasons,
        "query_plan":[{"dimension":d,"state":"UNRESOLVED","resolver":"NONE"} for d in REQUIRED_DIMENSIONS],
        "resolver_evidence":[],
        "material_records":[],
        "unresolved_dimensions":unresolved,
        "scope_coverage":{
            "required_query_dimensions_complete":False,
            "resolver_scope_complete":False,
            "negative_evidence_distinct_sources":0,
            "scope_qualified_negative_evidence_distinct_sources":0,
        },
        "similarity_analysis":"UNRESOLVED",
        "goods_relatedness":"UNRESOLVED",
        "evidence_hashes":[],
    }


def evaluate(request,request_schema,receipt_schema):
    sha=head()
    try:
        jsonschema.Draft202012Validator(request_schema).validate(request)
    except Exception:
        out=hold(request,sha,["REQUEST_SCHEMA_INVALID"],REQUIRED_DIMENSIONS)
        jsonschema.Draft202012Validator(receipt_schema).validate(out)
        return out

    missing=[d for d in REQUIRED_DIMENSIONS if d not in request["requested_scope"]["query_dimensions"]]
    if missing:
        out=hold(request,sha,["REQUEST_SCOPE_MISSING_REQUIRED_DIMENSIONS"],missing)
        jsonschema.Draft202012Validator(receipt_schema).validate(out)
        return out

    wording=request["wording"].strip()
    plan=build_query_plan(wording,[])
    cores=plan["CORE_DOMINANT_TOKEN"]["queries"]
    phonetic=plan["PHONETIC_OR_SPELLING_WHEN_MATERIAL"].get("queries") or []
    if not cores or not phonetic:
        out=hold(request,sha,["QUERY_PLAN_INCOMPLETE"],["CORE_DOMINANT_TOKEN","PHONETIC_OR_SPELLING_WHEN_MATERIAL"])
        jsonschema.Draft202012Validator(receipt_schema).validate(out)
        return out

    rows=[]
    positive_entries=[]
    dims={d:True for d in REQUIRED_DIMENSIONS}
    unresolved_transport=False
    tm_qualified=all(grammar_ok(core) for core in cores)

    executable=os.getenv("AVER_BROWSER_EXECUTABLE") or None
    with sync_playwright() as playwright:
        launch={"headless":True}
        if executable:
            launch["executable_path"]=executable
        browser=playwright.chromium.launch(**launch)
        trademarkia=TrademarkiaResolver(browser)

        def add(resolver,dimension,record):
            nonlocal unresolved_transport
            rows.append((resolver,dimension,record))
            unresolved_transport |= record["polarity"]=="UNRESOLVED"
            if record["polarity"]=="POSITIVE":
                positive_entries.append((resolver,dimension,record))

        def resolve_official(dimension,query,shared_component):
            record=usp(browser,query)
            if record["polarity"]=="POSITIVE":
                record["positive_review"]=review_official_positive(
                    browser,request,dimension,record,shared_component
                )
            add("USPTO_OFFICIAL_DIRECT_FIELDTAG",dimension,record)
            if record["polarity"]=="NEGATIVE":
                return True
            review=record.get("positive_review") or {}
            return bool(review.get("classification")==NONMATERIAL_PARTIAL and review.get("record_binding_complete"))

        dims["EXACT"] &= resolve_official("EXACT",oq(wording),wording)
        normalized=normalize_wording(wording)
        dims["NORMALIZED_EXACT"] &= resolve_official("NORMALIZED_EXACT",oq(normalized),normalized)
        for core in cores:
            dims["CORE_DOMINANT_TOKEN"] &= resolve_official("CORE_DOMINANT_TOKEN",oq(core),core)
            dims["EXPANDED_PARTIAL"] &= resolve_official("EXPANDED_PARTIAL",pq(core),core)
        for query in phonetic:
            dims["PHONETIC_OR_SPELLING_WHEN_MATERIAL"] &= resolve_official(
                "PHONETIC_OR_SPELLING_WHEN_MATERIAL",query,"PHONETIC_OR_SPELLING"
            )

        second=tm(trademarkia,wording)
        add("TRADEMARKIA_QUOTED_LITERAL","EXACT",second)
        tm_qualified &= second["polarity"]=="NEGATIVE" and second["bound"]
        for core in cores:
            second=tm(trademarkia,core)
            add("TRADEMARKIA_QUOTED_LITERAL","CORE_DOMINANT_TOKEN",second)
            tm_qualified &= second["polarity"]=="NEGATIVE" and second["bound"]
        browser.close()

    material_positive_entries=[]
    all_positive_bound=True
    material_records=[]
    nonmaterial_partial_count=0
    for resolver,dimension,record in positive_entries:
        review=record.get("positive_review") or {}
        bound=bool(review.get("record_binding_complete"))
        all_positive_bound &= bound
        if review.get("classification")==NONMATERIAL_PARTIAL and bound:
            nonmaterial_partial_count += 1
        else:
            material_positive_entries.append((resolver,dimension,record))

        detail=record.get("single_record_detail") or {}
        if detail.get("serial_number") and detail.get("mark_text"):
            status=(review.get("tsdr_status") or {}).get("state") or "POSITIVE_RECALL_STATUS_UNRESOLVED"
            if review.get("classification")==NONMATERIAL_PARTIAL:
                status="DEAD_INACTIVE_NONMATERIAL_EXPANDED_PARTIAL_RECALL"
            classes=",".join(detail.get("class_codes") or []) or "UNRESOLVED"
            goods=(detail.get("goods_services_excerpt") or "UNRESOLVED").strip()
            material_records.append({
                "mark_text":detail["mark_text"][:300],
                "status":status[:120],
                "identifier":str(detail["serial_number"])[:120],
                "class_or_goods_services_context":f"classes={classes}; goods={goods}"[:1200],
            })

    material_positive=bool(material_positive_entries)
    if not positive_entries:
        all_positive_bound=True

    dims["RELATED_GOODS_REVIEW"]=bool(
        all(dims[d] for d in REQUIRED_DIMENSIONS if d!="RELATED_GOODS_REVIEW")
        and not material_positive
    )

    unresolved=[d for d,value in dims.items() if not value]
    if material_positive:
        unresolved.append("MATERIAL_RECORD_BINDING_AND_RELATEDNESS_REVIEW")
    if not tm_qualified and not material_positive:
        unresolved.append("SECOND_SCOPE_QUALIFIED_NEGATIVE_SOURCE")
    unresolved=list(dict.fromkeys(unresolved))

    complete=all(dims.values()) and not material_positive
    qualified_sources=2 if complete and tm_qualified else 1 if complete else 0
    similarity="CLEAR" if complete else "UNRESOLVED"
    goods_relatedness="CLEAR" if complete else "UNRESOLVED"

    decision=evaluate_tm_state({
        "material_positive_record_present":material_positive,
        "record_binding_complete":all_positive_bound if material_positive else True,
        "similarity_assessment":similarity,
        "goods_relatedness_assessment":goods_relatedness,
        "required_query_dimensions_complete":complete,
        "resolver_scope_complete":complete,
        "unresolved_dimensions":unresolved,
        "negative_evidence_distinct_sources":2,
        "scope_qualified_negative_evidence_distinct_sources":qualified_sources,
        "transport_blocked":unresolved_transport,
        "control_blocked":False,
        "source_discordance":False,
    })

    reason_codes=list(decision["decision_reason_codes"])
    if nonmaterial_partial_count:
        reason_codes.append("NONMATERIAL_DEAD_UNRELATED_EXPANDED_PARTIAL_RECALL_BOUND")
    reason_codes=list(dict.fromkeys(reason_codes))

    evidence=[]
    hashes=[]
    for resolver,dimension,record in rows:
        evidence_record={
            "resolver":resolver,
            "dimension":dimension,
            "record":record,
        }
        digest=jhash(evidence_record)
        hashes.append(digest)
        state=record.get("state") or record.get("terminal") or "OBSERVED"
        review=record.get("positive_review") or {}
        if review.get("classification")==NONMATERIAL_PARTIAL:
            state="BOUND_NONMATERIAL_DEAD_UNRELATED_PARTIAL_RECALL"
        evidence.append({
            "resolver":resolver,
            "scope":f"{dimension}:{record['query']}"[:240],
            "state":state[:120],
            "evidence_polarity":record["polarity"],
            "evidence_hash":digest,
        })

    out={
        "schema":"AVER_TM_RECEIPT",
        "schema_version":"1.0",
        "engine_version":ENGINE_VERSION,
        "engine_commit_sha":sha,
        "request_id":request["request_id"],
        "request_sha256":jhash(request),
        "decision":decision["decision"],
        "confidence_label":decision["confidence_label"],
        "legal_clearance_asserted":False,
        "decision_reason_codes":reason_codes,
        "query_plan":[{
            "dimension":d,
            "state":"RESOLVED" if dims[d] else "UNRESOLVED",
            "resolver":"USPTO_OFFICIAL_DIRECT_FIELDTAG" if d!="RELATED_GOODS_REVIEW" else "A_VER_BOUND_RESULTSET_REVIEW",
        } for d in REQUIRED_DIMENSIONS],
        "resolver_evidence":evidence,
        "material_records":material_records,
        "unresolved_dimensions":unresolved,
        "scope_coverage":{
            "required_query_dimensions_complete":complete,
            "resolver_scope_complete":complete,
            "negative_evidence_distinct_sources":2,
            "scope_qualified_negative_evidence_distinct_sources":qualified_sources,
        },
        "similarity_analysis":similarity,
        "goods_relatedness":goods_relatedness,
        "evidence_hashes":list(dict.fromkeys(hashes)),
    }
    jsonschema.Draft202012Validator(receipt_schema).validate(out)
    return out


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--request",required=True)
    parser.add_argument("--output",required=True)
    parser.add_argument("--request-schema",default="spec/request.schema.json")
    parser.add_argument("--receipt-schema",default="spec/receipt.schema.json")
    args=parser.parse_args()
    request=json.loads(Path(args.request).read_text())
    out=evaluate(
        request,
        json.loads(Path(args.request_schema).read_text()),
        json.loads(Path(args.receipt_schema).read_text()),
    )
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(out,indent=2)+"\n")
    print(out["decision"],out["decision_reason_codes"],out["unresolved_dimensions"])


if __name__=="__main__":
    main()
