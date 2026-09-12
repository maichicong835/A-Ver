#!/usr/bin/env python3
import json, os, re
from datetime import datetime, timezone
from pathlib import Path

from acceptance_a2 import sha, norm, open_public_query_panel, choose_search_input, set_exact_mode, submit_query

ENGINE_VERSION='0.1.0'
HARNESS_REVISION='a3.2'
PHASE='A3_NEGATIVE_RESULTSET_SEMANTICS'
OUT=Path('artifacts/a3'); OUT.mkdir(parents=True,exist_ok=True)
SYNTHETIC_QUERY='QZXJVMRKPLN91372'

CANARIES=[
  {'resolver':'TMHUNT','url':'http://www.tmhunt.com/','query':SYNTHETIC_QUERY,'public_query_anchor':'#query','declared_scope':'IC025_ONLY'},
  {'resolver':'TRADEMARKIA','url':'https://www.trademarkia.com/trademark/search','query':SYNTHETIC_QUERY,'declared_scope':'US_FEDERAL_SEARCH_SURFACE_UI_DEFAULT'}
]

NEGATIVE_PATTERNS=[
  r'\bshowing\s+0\s+to\s+0\s+of\s+0\s+results\b',
  r'\b0\s+(?:search\s+)?(?:results?|trademarks?|records?|matches?)\b',
  r'\bno\s+(?:trademarks?|results?|records?|matches?)\s+(?:were\s+)?found\b',
  r'\bno\s+(?:trademark|trademarks)\s+found\b',
  r'\bno\s+results?\b',
  r'\bno\s+matching\s+(?:trademarks?|records?|results?)\b',
  r'\bno\s+exact\s+matches?\b',
  r'\bwe\s+couldn[’\']?t\s+find(?:\s+any)?\s+(?:trademarks?|results?|matches?)?\b',
  r'\bwe\s+could\s+not\s+find(?:\s+any)?\s+(?:trademarks?|results?|matches?)?\b',
  r'\bnothing\s+found\b'
]

def now(): return datetime.now(timezone.utc).isoformat()

def evidence_snippets(text):
    flat=norm(text)
    lower=flat.lower(); snippets=[]
    for pattern in NEGATIVE_PATTERNS:
        for m in re.finditer(pattern,lower,re.I):
            a=max(0,m.start()-180); b=min(len(flat),m.end()+280)
            snippets.append({'pattern':pattern,'text':flat[a:b]})
            if len(snippets)>=12: return snippets
    return snippets

def diagnostic_lines(text, query):
    lines=[]; seen=set()
    for raw in (text or '').splitlines():
        line=norm(raw)
        if not line: continue
        low=line.lower()
        if any(k in low for k in ['result','trademark','match','found','search']) or query.lower() in low:
            clipped=line[:500]
            if clipped not in seen:
                seen.add(clipped); lines.append(clipped)
        if len(lines)>=40: break
    return lines

def dom_result_structure(page):
    evidence={
      'visible_trademark_links':0,
      'visible_result_like_nodes':0,
      'empty_state_like_nodes':[],
      'total_count_like_texts':[]
    }
    try:
        links=page.locator('a:visible')
        count=0
        for i in range(min(links.count(),700)):
            href=links.nth(i).get_attribute('href') or ''
            if re.search(r'/trademark(?:s)?/',href,re.I) and '/search' not in href.lower():
                count+=1
        evidence['visible_trademark_links']=count
    except Exception:
        pass
    try:
        nodes=page.locator('[class*="result"]:visible, [data-testid*="result"]:visible, [class*="trademark"]:visible, [data-testid*="trademark"]:visible')
        evidence['visible_result_like_nodes']=min(nodes.count(),1000)
    except Exception:
        pass
    try:
        candidates=page.locator('div:visible, p:visible, span:visible, h1:visible, h2:visible, h3:visible')
        for i in range(min(candidates.count(),1600)):
            try: text=norm(candidates.nth(i).inner_text())
            except Exception: continue
            low=text.lower()
            if not text or len(text)>500: continue
            if any(x in low for x in ['no result','no trademark','no match','nothing found','couldn’t find','couldn\'t find','could not find']):
                evidence['empty_state_like_nodes'].append(text)
            if re.search(r'\b(?:about\s+)?\d[\d,]*\s+(?:results?|trademarks?|matches?)\b',low):
                evidence['total_count_like_texts'].append(text)
            if len(evidence['empty_state_like_nodes'])>=20 and len(evidence['total_count_like_texts'])>=20:
                break
        evidence['empty_state_like_nodes']=list(dict.fromkeys(evidence['empty_state_like_nodes']))[:20]
        evidence['total_count_like_texts']=list(dict.fromkeys(evidence['total_count_like_texts']))[:20]
    except Exception:
        pass
    return evidence

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
        page.wait_for_timeout(2800)
        after_text=page.locator('body').inner_text(timeout=10000); after_html=page.content(); lower=after_text.lower()
        captcha=any(x in lower for x in ['captcha','verify you are human','are you a robot','human verification'])
        query_in_page=canary['query'].lower() in lower
        query_in_url=canary['query'].lower() in page.url.lower()
        content_changed=sha(after_html)!=before_hash
        snippets=evidence_snippets(after_text)
        structure=dom_result_structure(page)
        structural_empty=bool(structure['empty_state_like_nodes'])
        zero_count=any(re.search(r'\b0\s+(?:results?|trademarks?|matches?)\b',t.lower()) for t in structure['total_count_like_texts'])
        query_execution_evidence=query_in_page or query_in_url or content_changed
        explicit_zero=bool(snippets) or structural_empty or zero_count
        rec.update({
          'final_url':page.url,'content_changed':content_changed,'query_visible_in_page':query_in_page,'query_bound_in_url':query_in_url,
          'query_execution_evidence':query_execution_evidence,'explicit_negative_semantics_observed':explicit_zero,
          'negative_semantics_snippets':snippets,'dom_result_structure':structure,'diagnostic_lines':diagnostic_lines(after_text,canary['query']),
          'captcha_or_human_control_observed':captcha,'after_body_sha256':sha(after_html),'after_text_sha256':sha(after_text),
          'network_response_sample':responses[:120]
        })
        if captcha:
            rec['state']='A3_CONTROL_BLOCKED'; rec['failure_signature']='HUMAN_VERIFICATION_OR_CAPTCHA_OBSERVED'
        elif query_execution_evidence and explicit_zero:
            rec['state']='A3_NEGATIVE_SEMANTICS_PASS'
        else:
            rec['failure_signature']='NATIVE_QUERY_EXECUTED_BUT_EXPLICIT_ZERO_SEMANTICS_NOT_MACHINE_BOUND_AFTER_OPAQUE_CANARY'
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
      'schema':'AVER_ACCEPTANCE_RECEIPT','engine_version':ENGINE_VERSION,'harness_revision':HARNESS_REVISION,'mode':'ACCEPTANCE_ONLY','phase':PHASE,
      'authority':{'repository':os.getenv('GITHUB_REPOSITORY','UNKNOWN'),'commit_sha':os.getenv('GITHUB_SHA','UNKNOWN'),'workflow_run_id':os.getenv('GITHUB_RUN_ID','UNKNOWN'),'workflow_run_attempt':os.getenv('GITHUB_RUN_ATTEMPT','UNKNOWN')},
      'browser_executable':executable,'started_at_utc':started,'finished_at_utc':now(),'phase_state':phase,'resolver_states':states,
      'synthetic_fixed_canary':SYNTHETIC_QUERY,'synthetic_canary_design':'OPAQUE_SINGLE_TOKEN_TO_AVOID_BROAD_FUZZY_TOKEN_EXPANSION','daily7_candidate_queries_executed':False,
      'production_tm_decision_authorized':False,'external_side_effects_authorized':False,
      'negative_clearance_inferred_for_any_real_candidate':False,
      'scope_law':'TMHUNT_NEGATIVE_EVIDENCE_IS_IC025_ONLY;_TRADEMARKIA_NEGATIVE_EVIDENCE_IS_LIMITED_TO_THE_MACHINE_BOUND_UI_QUERY_SCOPE_AND_FILTERS',
      'records':records,
      'next_action':'PROCEED_TO_A4_REPEATABILITY_AND_RESOLVER_MODE_MATRIX;_DO_NOT_PROMOTE_YET' if phase=='A3_PASS' else 'HOLD_ANY_RESOLVER_NEGATIVE_CAPABILITY_THAT_REMAINS_UNPROVEN;_DO_NOT_RETRY_SAME_STRATEGY_OR_QUERY_REAL_CANDIDATES'
    }
    (OUT/'a3-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'phase_state':phase,'resolver_states':states,'synthetic_query':SYNTHETIC_QUERY},indent=2)); return 0

if __name__=='__main__': raise SystemExit(main())
