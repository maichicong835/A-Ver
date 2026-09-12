#!/usr/bin/env python3
import json, os, re
from datetime import datetime, timezone
from pathlib import Path

from acceptance_a2 import sha, norm, open_public_query_panel, choose_search_input, set_exact_mode, submit_query

ENGINE_VERSION='0.1.0'
PHASE='A3_NEGATIVE_RESULTSET_SEMANTICS'
OUT=Path('artifacts/a3'); OUT.mkdir(parents=True,exist_ok=True)
SYNTHETIC_QUERY='AVER QZXJ KESTREL 91372'

CANARIES=[
  {'resolver':'TMHUNT','url':'http://www.tmhunt.com/','query':SYNTHETIC_QUERY,'public_query_anchor':'#query','declared_scope':'IC025_ONLY'},
  {'resolver':'TRADEMARKIA','url':'https://www.trademarkia.com/trademark/search','query':SYNTHETIC_QUERY,'declared_scope':'US_FEDERAL_SEARCH_SURFACE_UI_DEFAULT'}
]

NEGATIVE_PATTERNS=[
  r'\b0\s+(?:search\s+)?(?:results?|trademarks?|records?|matches?)\b',
  r'\bno\s+(?:trademarks?|results?|records?|matches?)\s+(?:were\s+)?found\b',
  r'\bno\s+results?\b',
  r'\bno\s+matching\s+(?:trademarks?|records?|results?)\b',
  r'\bwe\s+couldn[’\']?t\s+find\b'
]

def now(): return datetime.now(timezone.utc).isoformat()

def evidence_snippets(text):
    flat=norm(text)
    lower=flat.lower(); snippets=[]
    for pattern in NEGATIVE_PATTERNS:
        for m in re.finditer(pattern,lower,re.I):
            a=max(0,m.start()-180); b=min(len(flat),m.end()+260)
            snippets.append({'pattern':pattern,'text':flat[a:b]})
            if len(snippets)>=12: return snippets
    return snippets

def run_negative(browser,canary):
    page=browser.new_page(viewport={'width':1440,'height':1000})
    responses=[]
    page.on('response',lambda r: responses.append({'url':r.url[:300],'status':r.status}) if len(responses)<120 else None)
    rec={'resolver':canary['resolver'],'query':canary['query'],'declared_scope':canary['declared_scope'],'state':'A3_NEGATIVE_SEMANTICS_UNPROVEN','failure_signature':None}
    try:
        page.goto(canary['url'],wait_until='domcontentloaded',timeout=30000); page.wait_for_timeout(1500)
        rec['public_query_panel']=open_public_query_panel(page,canary)
        before_html=page.content(); before_hash=sha(before_html)
        selected,inputs=choose_search_input(page); rec['input_candidates']=inputs[:30]
        if not selected:
            rec['failure_signature']='VISIBLE_SEARCH_INPUT_NOT_FOUND'; return rec
        input_el,input_desc=selected; rec['selected_input']=input_desc
        exact=set_exact_mode(page); rec['exact_mode_control']=exact
        if canary['resolver']=='TMHUNT':
            rec['query_mode_binding']='EXACT' if exact.get('select') or exact.get('clicked_label') else 'UI_MODE_UNBOUND'
        else:
            rec['query_mode_binding']='UI_DEFAULT'
        input_el.fill(canary['query'])
        rec['submission']=submit_query(page,input_el,before_hash)
        page.wait_for_timeout(2200)
        after_text=page.locator('body').inner_text(timeout=10000); after_html=page.content(); lower=after_text.lower()
        captcha=any(x in lower for x in ['captcha','verify you are human','are you a robot','human verification'])
        query_in_page=canary['query'].lower() in lower
        query_in_url=canary['query'].lower().replace(' ','+') in page.url.lower() or canary['query'].lower().replace(' ','%20') in page.url.lower()
        content_changed=sha(after_html)!=before_hash
        snippets=evidence_snippets(after_text)
        query_execution_evidence=query_in_page or query_in_url or content_changed
        explicit_zero=bool(snippets)
        rec.update({
          'final_url':page.url,'content_changed':content_changed,'query_visible_in_page':query_in_page,'query_bound_in_url':query_in_url,
          'query_execution_evidence':query_execution_evidence,'explicit_negative_semantics_observed':explicit_zero,
          'negative_semantics_snippets':snippets,'captcha_or_human_control_observed':captcha,
          'after_body_sha256':sha(after_html),'network_response_sample':responses[:120]
        })
        if captcha:
            rec['state']='A3_CONTROL_BLOCKED'; rec['failure_signature']='HUMAN_VERIFICATION_OR_CAPTCHA_OBSERVED'
        elif query_execution_evidence and explicit_zero:
            rec['state']='A3_NEGATIVE_SEMANTICS_PASS'
        else:
            rec['failure_signature']='NATIVE_QUERY_EXECUTED_BUT_EXPLICIT_ZERO_SEMANTICS_NOT_MACHINE_BOUND'
    except Exception as e:
        rec['state']='A3_BROWSER_TRANSPORT_BLOCKED'; rec['failure_signature']=f'{type(e).__name__}:{str(e)[:240]}'
    finally:
        page.close()
    return rec

def main():
    from playwright.sync_api import sync_playwright
    started=now(); executable=os.getenv('AVER_BROWSER_EXECUTABLE') or None
    with sync_playwright() as p:
        launch={'headless':True}
        if executable: launch['executable_path']=executable
        browser=p.chromium.launch(**launch); records=[run_negative(browser,c) for c in CANARIES]; browser.close()
    states={r['resolver']:r['state'] for r in records}
    if all(v=='A3_NEGATIVE_SEMANTICS_PASS' for v in states.values()): phase='A3_PASS'
    elif any(v=='A3_NEGATIVE_SEMANTICS_PASS' for v in states.values()): phase='A3_PARTIAL'
    else: phase='A3_BLOCKED'
    receipt={
      'schema':'AVER_ACCEPTANCE_RECEIPT','engine_version':ENGINE_VERSION,'mode':'ACCEPTANCE_ONLY','phase':PHASE,
      'authority':{'repository':os.getenv('GITHUB_REPOSITORY','UNKNOWN'),'commit_sha':os.getenv('GITHUB_SHA','UNKNOWN'),'workflow_run_id':os.getenv('GITHUB_RUN_ID','UNKNOWN'),'workflow_run_attempt':os.getenv('GITHUB_RUN_ATTEMPT','UNKNOWN')},
      'browser_executable':executable,'started_at_utc':started,'finished_at_utc':now(),'phase_state':phase,'resolver_states':states,
      'synthetic_fixed_canary':SYNTHETIC_QUERY,'daily7_candidate_queries_executed':False,
      'production_tm_decision_authorized':False,'external_side_effects_authorized':False,
      'negative_clearance_inferred_for_any_real_candidate':False,
      'scope_law':'TMHUNT_NEGATIVE_EVIDENCE_IS_IC025_ONLY;_TRADEMARKIA_NEGATIVE_EVIDENCE_IS_LIMITED_TO_THE_MACHINE_BOUND_UI_QUERY_SCOPE_AND_FILTERS',
      'records':records,
      'next_action':'PROCEED_TO_A4_REPEATABILITY_AND_RESOLVER_MODE_MATRIX;_DO_NOT_PROMOTE_YET' if phase=='A3_PASS' else 'REPAIR_ONLY_FAILED_NEGATIVE_SEMANTICS_BINDING;_DO_NOT_QUERY_REAL_CANDIDATES_OR_EXPAND_BREADTH'
    }
    (OUT/'a3-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'phase_state':phase,'resolver_states':states,'synthetic_query':SYNTHETIC_QUERY},indent=2)); return 0

if __name__=='__main__': raise SystemExit(main())
