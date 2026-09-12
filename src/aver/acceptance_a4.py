#!/usr/bin/env python3
import json, os, re
from datetime import datetime, timezone
from pathlib import Path

from acceptance_a2 import sha, norm, open_public_query_panel, choose_search_input, submit_query

ENGINE_VERSION='0.1.0'
PHASE='A4_REPEATABILITY_AND_MODE_MATRIX'
OUT=Path('artifacts/a4'); OUT.mkdir(parents=True,exist_ok=True)

def now(): return datetime.now(timezone.utc).isoformat()

def click_exact_text(page,text):
    evidence={'target':text,'clicked':False,'method':None}
    for selector in [f'label:has-text("{text}")',f'button:has-text("{text}")',f'a:has-text("{text}")',f'text="{text}"']:
        try:
            loc=page.locator(selector).filter(visible=True) if False else page.locator(selector)
            for i in range(min(loc.count(),20)):
                if not loc.nth(i).is_visible(): continue
                loc.nth(i).click(); page.wait_for_timeout(700)
                evidence.update({'clicked':True,'method':selector}); return evidence
        except Exception:
            continue
    return evidence

def tmhunt_mode(browser,mode,query,expect):
    page=browser.new_page(viewport={'width':1440,'height':1000})
    rec={'resolver':'TMHUNT','mode':mode,'query':query,'expect':expect,'state':'MODE_UNPROVEN','failure_signature':None}
    try:
        page.goto('http://www.tmhunt.com/',wait_until='domcontentloaded',timeout=30000); page.wait_for_timeout(1200)
        rec['query_panel']=open_public_query_panel(page,{'public_query_anchor':'#query','url':'http://www.tmhunt.com/'})
        if mode in ('EXACT','PARTIAL'):
            rec['mode_control']=click_exact_text(page,'Exact Match' if mode=='EXACT' else 'Partial Match')
        elif mode=='SPLIT':
            rec['mode_control']=click_exact_text(page,'Split Search')
        elif mode=='WILDCARD':
            rec['mode_control']=click_exact_text(page,'Wildcard Search')
        selected,inputs=choose_search_input(page); rec['input_candidates']=inputs[:20]
        if not selected:
            rec['failure_signature']='VISIBLE_SEARCH_INPUT_NOT_FOUND'; return rec
        input_el,_=selected; before=sha(page.content()); input_el.fill(query); rec['submission']=submit_query(page,input_el,before)
        page.wait_for_timeout(2400)
        text=norm(page.locator('body').inner_text(timeout=10000))
        totals=[int(x.replace(',','')) for x in re.findall(r'Showing\s+\d+\s+to\s+\d+\s+of\s+([\d,]+)\s+results',text,re.I)]
        rec['result_totals']=totals[:20]
        rec['body_sha256']=sha(page.content())
        if expect=='POSITIVE' and totals and max(totals)>0:
            rec['state']='MODE_PASS'
        elif expect=='ZERO' and totals and max(totals)==0:
            rec['state']='MODE_PASS'
        else:
            rec['failure_signature']='TMHUNT_RESULT_TOTAL_NOT_MATCH_EXPECTATION'
    except Exception as e:
        rec['state']='MODE_BLOCKED'; rec['failure_signature']=f'{type(e).__name__}:{str(e)[:220]}'
    finally:
        page.close()
    return rec

def trademarkia_query(browser,kind,query,expected_identifier=None):
    page=browser.new_page(viewport={'width':1440,'height':1000})
    rec={'resolver':'TRADEMARKIA','mode':kind,'query':query,'state':'MODE_UNPROVEN','failure_signature':None}
    try:
        page.goto('https://www.trademarkia.com/trademark/search',wait_until='domcontentloaded',timeout=30000); page.wait_for_timeout(1400)
        selected,inputs=choose_search_input(page); rec['input_candidates']=inputs[:20]
        if not selected:
            rec['failure_signature']='VISIBLE_SEARCH_INPUT_NOT_FOUND'; return rec
        input_el,_=selected; before=sha(page.content()); input_el.fill(query); rec['submission']=submit_query(page,input_el,before)
        page.wait_for_timeout(2600)
        text=norm(page.locator('body').inner_text(timeout=10000)); lower=text.lower()
        count_match=re.search(r'([\d,]+)\s+trademarks?\s+found\s+for',text,re.I)
        total=int(count_match.group(1).replace(',','')) if count_match else None
        no_results='no results' in lower
        identifier_seen=expected_identifier in text if expected_identifier else None
        rec.update({'final_url':page.url,'reported_total':total,'no_results_marker':no_results,'expected_identifier':expected_identifier,'expected_identifier_seen':identifier_seen,'body_sha256':sha(page.content())})
        if kind=='KNOWN_POSITIVE' and ((identifier_seen is True) or (total is not None and total>0)):
            rec['state']='MODE_PASS'
        elif kind=='OPAQUE_ZERO' and no_results:
            rec['state']='MODE_PASS'
        elif kind=='FUZZY_RECALL' and total is not None and total>0:
            rec['state']='MODE_PASS'
        else:
            rec['failure_signature']='TRADEMARKIA_RESULT_SEMANTICS_NOT_MATCH_EXPECTATION'
    except Exception as e:
        rec['state']='MODE_BLOCKED'; rec['failure_signature']=f'{type(e).__name__}:{str(e)[:220]}'
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
        records=[
          tmhunt_mode(browser,'EXACT','NIKE','POSITIVE'),
          tmhunt_mode(browser,'PARTIAL','NIKE','POSITIVE'),
          tmhunt_mode(browser,'SPLIT','NIKE SHOES','POSITIVE'),
          tmhunt_mode(browser,'WILDCARD','NIK*','POSITIVE'),
          tmhunt_mode(browser,'EXACT','QZXJVMRKPLN91372','ZERO'),
          trademarkia_query(browser,'KNOWN_POSITIVE','JUST DO IT','50086105'),
          trademarkia_query(browser,'OPAQUE_ZERO','QZXJVMRKPLN91372'),
          trademarkia_query(browser,'FUZZY_RECALL','AVER QZXJ KESTREL 91372')
        ]
        browser.close()
    tmhunt=[r for r in records if r['resolver']=='TMHUNT']; tria=[r for r in records if r['resolver']=='TRADEMARKIA']
    states={
      'TMHUNT_MODE_MATRIX':'PASS' if all(r['state']=='MODE_PASS' for r in tmhunt) else 'PARTIAL',
      'TRADEMARKIA_BEHAVIOR_MATRIX':'PASS' if all(r['state']=='MODE_PASS' for r in tria) else 'PARTIAL'
    }
    phase='A4_PASS' if all(v=='PASS' for v in states.values()) else 'A4_PARTIAL'
    receipt={
      'schema':'AVER_ACCEPTANCE_RECEIPT','engine_version':ENGINE_VERSION,'mode':'ACCEPTANCE_ONLY','phase':PHASE,
      'authority':{'repository':os.getenv('GITHUB_REPOSITORY','UNKNOWN'),'commit_sha':os.getenv('GITHUB_SHA','UNKNOWN'),'workflow_run_id':os.getenv('GITHUB_RUN_ID','UNKNOWN'),'workflow_run_attempt':os.getenv('GITHUB_RUN_ATTEMPT','UNKNOWN')},
      'browser_executable':executable,'started_at_utc':started,'finished_at_utc':now(),'phase_state':phase,'resolver_states':states,
      'production_tm_decision_authorized':False,'external_side_effects_authorized':False,'daily7_candidate_queries_executed':False,
      'tmhunt_scope_law':'IC025_ONLY','trademarkia_role_law':'BROAD_RECALL_AND_RECORD_DISCOVERY;_OPAQUE_ZERO_SEMANTICS_DOES_NOT_TURN_FUZZY_MULTI_TOKEN_SEARCH_INTO_EXACT_CLEARANCE',
      'records':records,
      'repeatability_identity':{'run_id':os.getenv('GITHUB_RUN_ID','UNKNOWN'),'commit_sha':os.getenv('GITHUB_SHA','UNKNOWN')},
      'next_action':'REQUIRE_SECOND_DISTINCT_A4_RUN_WITH_SAME_HARNESS_AND_AUTHORITY_FILES_BEFORE_PROMOTION_REVIEW' if phase=='A4_PASS' else 'REPAIR_ONLY_FAILED_MODE;_NO_PRODUCTION_PROMOTION'
    }
    (OUT/'a4-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'phase_state':phase,'resolver_states':states,'record_states':[(r['resolver'],r['mode'],r['state']) for r in records]},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
