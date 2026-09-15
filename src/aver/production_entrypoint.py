#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import jsonschema
from aver.query_plan import build_query_plan
from aver.production import evaluate, grammar_ok, head, hold


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--request',required=True)
    ap.add_argument('--output',required=True)
    ap.add_argument('--request-schema',default='spec/request.schema.json')
    ap.add_argument('--receipt-schema',default='spec/receipt.schema.json')
    a=ap.parse_args()
    req=json.loads(Path(a.request).read_text())
    rs=json.loads(Path(a.request_schema).read_text())
    oschema=json.loads(Path(a.receipt_schema).read_text())
    try:
        jsonschema.Draft202012Validator(rs).validate(req)
    except Exception:
        out=hold(req,head(),['REQUEST_SCHEMA_INVALID'],['REQUEST_SCHEMA'])
    else:
        wording=req['wording'].strip()
        plan=build_query_plan(wording,[])
        cores=list(plan['CORE_DOMINANT_TOKEN'].get('queries') or [])
        if not cores or not all(grammar_ok(c) for c in cores):
            out=hold(req,head(),['SECOND_SOURCE_GRAMMAR_UNSUPPORTED'],['SECOND_SCOPE_QUALIFIED_NEGATIVE_SOURCE'])
        else:
            out=evaluate(req,rs,oschema)
    jsonschema.Draft202012Validator(oschema).validate(out)
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,indent=2)+'\n')
    print(out['decision'],out['decision_reason_codes'],out['unresolved_dimensions'])

if __name__=='__main__': main()
