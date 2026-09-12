#!/usr/bin/env python3
import hashlib, json, os, re, shutil, sys
from datetime import datetime, timezone
from pathlib import Path

ENGINE_VERSION='0.1.0'
PHASE='A2_QUERY_RESULTSET_SEMANTICS'
OUT=Path('artifacts/a2'); OUT.mkdir(parents=True,exist_ok=True)

CANARIES=[
  {'resolver':'TMHUNT','url':'http://www.tmhunt.com/','query':'NIKE','expected_identifiers':[]},
  {'resolver':'TRADEMARKIA','url':'https://www.trademarkia.com/trademark/search','query':'JUST DO IT','expected_identifiers':['50086105']}
]

def now(): return datetime.now(timezone.utc).isoformat()
def sha(s): return hashlib.sha256(s.encode('utf-8',errors='ignore')).hexdigest()
def norm(s): return re.sub(r'\s+',' ',s or '').strip()

def attr(locator,name):
    try: return locator.get_attribute(name)
    except Exception: return None

def choose_search_input(page):
    loc=page.locator('input:visible')
    best=None; best_score=-1; desc=[]
    for i in range(loc.count()):
        el=loc.nth(i)
        d={k:attr(el,k) for k in ['id','name','type','placeholder','aria-label']}
        typ=(d.get('type') or 'text').lower()
        if typ in {'hidden','checkbox','radio','submit','button','image','file'}: continue
        blob=' '.join(str(d.get(k) or '') for k in d).lower()
        score=0
        if typ=='search': score+=8
        for token,weight in [('search',7),('query',7),('mark',5),('phrase',4),('keyword',4),('word',2)]:
            if token in blob: score+=weight
        if i==0: score+=1
        desc.append({'index':i,'score':score,**d})
        if score>best_score: best=(el,d); best_score=score
    return best,desc

def set_exact_mode(page):
    evidence={'select':None,'clicked_label':None}
    selects=page.locator('select:visible')
    for i in range(selects.count()):
        s=selects.nth(i)
        try:
            options=s.locator('option').all_text_contents()
        except Exception:
            options=[]
        for text in options:
            if 'exact' in text.lower():
                try:
                    s.select_option(label=text)
                    evidence['select']={'index':i,'selected':text,'options':options[:20]}
                    return evidence
                except Exception:
                    pass
    labels=page.locator('label:visible')
    for i in range(labels.count()):
        text=norm(labels.nth(i).inner_text())
        if 'exact' in text.lower():
            try:
                labels.nth(i).click()
                evidence['clicked_label']=text[:120]
                return evidence
            except Exception:
                pass
    return evidence

def submit_query(page,input_el):
    evidence={'method':None,'control':None}
    buttons=page.locator('button:visible, input[type=submit]:visible, input[type=button]:visible')
    ranked=[]
    for i in range(buttons.count()):
        b=buttons.nth(i)
        try: text=norm(b.inner_text())
        except Exception: text=''
        blob=' '.join([text,attr(b,'value') or '',attr(b,'aria-label') or '',attr(b,'id') or '',attr(b,'name') or '']).lower()
        score=sum(w for token,w in [('search',8),('find',6),('hunt',5),('submit',3),('go',2)] if token in blob)
        ranked.append((score,i,blob[:140]))
    ranked.sort(reverse=True)
    if ranked and ranked[0][0]>0:
        score,i,blob=ranked[0]
        try:
            buttons.nth(i).click(); evidence={'method':'CLICK','control':blob,'score':score}; return evidence
        except Exception:
            pass
    input_el.press('Enter'); evidence={'method':'ENTER','control':'SEARCH_INPUT'}; return evidence

def run_canary(browser,canary):
    page=browser.new_page(viewport={'width':1440,'height':1000})
    responses=[]
    def on_response(r):
        try:
            if len(responses)<80:
                responses.append({'url':r.url[:300],'status':r.status})
        except Exception: pass
    page.on('response',on_response)
    rec={'resolver':canary['resolver'],'query':canary['query'],'url':canary['url'],'state':'A2_NATIVE_QUERY_UNRESOLVED','failure_signature':None}
    try:
        page.goto(canary['url'],wait_until='domcontentloaded',timeout=30000)
        page.wait_for_timeout(1800)
        before_text=page.locator('body').inner_text(timeout=10000)
        before_html=page.content()
        before_count=before_text.lower().count(canary['query'].lower())
        selected,inputs=choose_search_input(page)
        rec['input_candidates']=inputs[:30]
        if not selected:
            rec['failure_signature']='VISIBLE_SEARCH_INPUT_NOT_FOUND'; return rec
        input_el,input_desc=selected
        rec['selected_input']=input_desc
        exact=set_exact_mode(page); rec['exact_mode_control']=exact
        input_el.fill(canary['query'])
        rec['submission']=submit_query(page,input_el)
        page.wait_for_timeout(2500)
        after_text=page.locator('body').inner_text(timeout=10000)
        after_html=page.content()
        lower_after=after_text.lower()
        captcha=any(x in lower_after for x in ['captcha','verify you are human','are you a robot','human verification'])
        if captcha:
            rec['state']='A2_CONTROL_BLOCKED'; rec['failure_signature']='HUMAN_VERIFICATION_OR_CAPTCHA_OBSERVED'
        after_count=lower_after.count(canary['query'].lower())
        result_links=[]
        links=page.locator('a:visible')
        for i in range(min(links.count(),400)):
            try: text=norm(links.nth(i).inner_text())
            except Exception: continue
            if canary['query'].lower() in text.lower(): result_links.append(text[:220])
        identifiers={x:(x in after_text or x in after_html) for x in canary['expected_identifiers']}
        content_changed=sha(before_html)!=sha(after_html)
        query_evidence=(after_count>before_count) or bool(result_links) or (identifiers and any(identifiers.values()))
        rec.update({
          'before_body_sha256':sha(before_html),'after_body_sha256':sha(after_html),'content_changed':content_changed,
          'before_query_text_count':before_count,'after_query_text_count':after_count,'result_link_samples':result_links[:20],
          'expected_identifier_observed':identifiers,'final_url':page.url,'same_page_url':page.url==canary['url'],
          'query_evidence_observed':query_evidence,'captcha_or_human_control_observed':captcha,
          'network_response_sample':responses[:80]
        })
        if not captcha and content_changed and query_evidence:
            rec['state']='A2_NATIVE_QUERY_PASS'
        elif not captcha:
            rec['failure_signature']=rec['failure_signature'] or 'QUERY_SUBMITTED_BUT_RESULTSET_EVIDENCE_NOT_STRONG_ENOUGH'
    except Exception as e:
        rec['state']='A2_BROWSER_TRANSPORT_BLOCKED'; rec['failure_signature']=f'{type(e).__name__}:{str(e)[:240]}'
    finally:
        page.close()
    return rec

def main():
    from playwright.sync_api import sync_playwright
    started=now(); executable=os.getenv('AVER_BROWSER_EXECUTABLE') or None
    with sync_playwright() as p:
        launch={'headless':True}
        if executable: launch['executable_path']=executable
        browser=p.chromium.launch(**launch)
        records=[run_canary(browser,c) for c in CANARIES]
        browser.close()
    states={r['resolver']:r['state'] for r in records}
    if all(s=='A2_NATIVE_QUERY_PASS' for s in states.values()): phase='A2_PASS'
    elif any(s=='A2_NATIVE_QUERY_PASS' for s in states.values()): phase='A2_PARTIAL'
    else: phase='A2_BLOCKED'
    receipt={
      'schema':'AVER_ACCEPTANCE_RECEIPT','engine_version':ENGINE_VERSION,'mode':'ACCEPTANCE_ONLY','phase':PHASE,
      'authority':{'repository':os.getenv('GITHUB_REPOSITORY','UNKNOWN'),'commit_sha':os.getenv('GITHUB_SHA','UNKNOWN'),'workflow_run_id':os.getenv('GITHUB_RUN_ID','UNKNOWN'),'workflow_run_attempt':os.getenv('GITHUB_RUN_ATTEMPT','UNKNOWN')},
      'browser_executable':executable,'started_at_utc':started,'finished_at_utc':now(),'phase_state':phase,'resolver_states':states,
      'production_tm_decision_authorized':False,'external_side_effects_authorized':False,'daily7_candidate_queries_executed':False,'negative_clearance_inferred':False,
      'known_positive_canaries_only':True,'records':records,
      'next_action':'PROCEED_TO_A3_CONTROLLED_NEGATIVE_SEMANTICS_WITH_FIXED_SYNTHETIC_CANARIES' if phase=='A2_PASS' else 'REPAIR_ONLY_FAILED_RESOLVER_BROWSER_QUERY_LAYER;_DO_NOT_EXPAND_CANARY_BREADTH'
    }
    (OUT/'a2-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'phase_state':phase,'resolver_states':states,'browser_executable':executable},indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
