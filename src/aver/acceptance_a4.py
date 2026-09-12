#!/usr/bin/env python3
import json, os, re, time
from datetime import datetime, timezone
from pathlib import Path

from acceptance_a2 import sha, norm, open_public_query_panel, choose_search_input, submit_query

ENGINE_VERSION='0.1.0'
HARNESS_REVISION='a4.1-causal-repair'
PHASE='A4_REPEATABILITY_AND_MODE_MATRIX'
OUT=Path('artifacts/a4'); OUT.mkdir(parents=True,exist_ok=True)

MODE_LABELS={
  'EXACT':'Exact Match',
  'PARTIAL':'Partial Match',
  'SPLIT':'Split Search',
  'WILDCARD':'Wildcard Search'
}

def now(): return datetime.now(timezone.utc).isoformat()

def safe_text(locator, limit=1200):
    try:
        return norm(locator.inner_text(timeout=3000))[:limit]
    except Exception:
        return ''

def visible_attrs(locator):
    try:
        return locator.evaluate("""el => ({
          tag: el.tagName,
          id: el.id || null,
          name: el.getAttribute('name'),
          value: el.getAttribute('value'),
          type: el.getAttribute('type'),
          role: el.getAttribute('role'),
          ariaSelected: el.getAttribute('aria-selected'),
          ariaPressed: el.getAttribute('aria-pressed'),
          ariaChecked: el.getAttribute('aria-checked'),
          className: el.className || null
        })""")
    except Exception:
        return {}

def panel_locator(page):
    panel=page.locator('#query')
    try:
        if panel.count() and panel.first.is_visible():
            return panel.first
    except Exception:
        pass
    return page.locator('body')

def click_mode_control(page, panel, mode):
    target=MODE_LABELS[mode]
    evidence={'target':target,'clicked':False,'method':None,'element':None}
    selectors=[
      f'label:has-text("{target}")',
      f'button:has-text("{target}")',
      f'a:has-text("{target}")',
      f'[role="tab"]:has-text("{target}")',
      f'text="{target}"'
    ]
    for root_name,root in [('panel',panel),('page',page)]:
        for selector in selectors:
            try:
                loc=root.locator(selector)
                for i in range(min(loc.count(),20)):
                    el=loc.nth(i)
                    if not el.is_visible(): continue
                    evidence['element']={'text':safe_text(el,300),'attrs':visible_attrs(el),'root':root_name}
                    el.click()
                    page.wait_for_timeout(450)
                    evidence.update({'clicked':True,'method':f'{root_name}:{selector}'})
                    return evidence
            except Exception:
                continue
    return evidence

def attest_active_mode(page, panel, mode):
    target=MODE_LABELS[mode]
    token=mode.lower()
    snapshots=[]
    selectors=[
      'input:checked',
      '[aria-selected="true"]',
      '[aria-pressed="true"]',
      '[aria-checked="true"]',
      '.active',
      '.selected',
      'option:checked'
    ]
    for selector in selectors:
        try:
            loc=panel.locator(selector)
            for i in range(min(loc.count(),40)):
                el=loc.nth(i)
                if not el.is_visible() and selector not in ('input:checked','option:checked'):
                    continue
                item={'selector':selector,'text':safe_text(el,400),'attrs':visible_attrs(el)}
                try:
                    if selector=='input:checked':
                        eid=el.get_attribute('id')
                        if eid:
                            lab=panel.locator(f'label[for="{eid}"]')
                            if lab.count():
                                item['label_text']=safe_text(lab.first,300)
                    parent=el.locator('xpath=..')
                    item['parent_text']=safe_text(parent,500)
                except Exception:
                    pass
                snapshots.append(item)
        except Exception:
            continue

    def blob(x):
        return norm(json.dumps(x,sort_keys=True)).lower()

    matched=[x for x in snapshots if token in blob(x) or target.lower() in blob(x)]
    if matched:
        return {'attested':True,'method':'ACTIVE_OR_CHECKED_MARKER','target':target,'matched':matched[:8],'snapshots':snapshots[:20]}

    selected,_=choose_panel_search_input(panel)
    if selected:
        el,_desc=selected
        context=[]
        try:
            form=el.locator('xpath=ancestor::form[1]')
            if form.count():
                context.append({'kind':'form','text':safe_text(form.first,900),'attrs':visible_attrs(form.first)})
        except Exception:
            pass
        try:
            node=el.locator('xpath=ancestor::*[contains(@class,"tab-pane") or contains(@class,"panel") or contains(@class,"content")][1]')
            if node.count():
                context.append({'kind':'mode_container','text':safe_text(node.first,900),'attrs':visible_attrs(node.first)})
        except Exception:
            pass
        context_blob=norm(json.dumps(context,sort_keys=True)).lower()
        if token in context_blob or target.lower() in context_blob:
            return {'attested':True,'method':'VISIBLE_MODE_CONTAINER_BOUND_TO_SEARCH_INPUT','target':target,'matched':context[:4],'snapshots':snapshots[:20]}

    return {'attested':False,'method':None,'target':target,'matched':[],'snapshots':snapshots[:20]}

def describe_input(el):
    d=visible_attrs(el)
    try: d['placeholder']=el.get_attribute('placeholder')
    except Exception: pass
    try: d['value_now']=el.input_value(timeout=1500)
    except Exception: pass
    return d

def choose_panel_search_input(panel):
    candidates=[]
    selectors=['textarea','input[type="search"]','input[type="text"]','input:not([type])']
    for selector in selectors:
        try:
            loc=panel.locator(selector)
            for i in range(min(loc.count(),30)):
                el=loc.nth(i)
                if not el.is_visible(): continue
                desc=describe_input(el)
                candidates.append((el,desc))
        except Exception:
            continue
    if not candidates:
        return None,[]
    def score(desc):
        s=0
        if desc.get('tag')=='TEXTAREA': s+=5
        if desc.get('type')=='search': s+=5
        txt=' '.join(str(desc.get(k) or '') for k in ('id','name','placeholder')).lower()
        if any(k in txt for k in ('search','query','mark','trademark')): s+=3
        return s
    candidates.sort(key=lambda x:score(x[1]),reverse=True)
    return candidates[0],[d for _,d in candidates]

def form_signature(input_el, panel):
    info={'scope':'panel','form_found':False,'action':None,'method':None,'hidden_inputs':[],'submit_controls':[]}
    form=None
    try:
        f=input_el.locator('xpath=ancestor::form[1]')
        if f.count():
            form=f.first
            info['form_found']=True
            info['action']=form.get_attribute('action')
            info['method']=form.get_attribute('method')
            h=form.locator('input[type="hidden"]')
            for i in range(min(h.count(),30)):
                info['hidden_inputs'].append(visible_attrs(h.nth(i)))
            submits=form.locator('button, input[type="submit"], input[type="button"]')
            for i in range(min(submits.count(),20)):
                s=submits.nth(i)
                if s.is_visible():
                    info['submit_controls'].append({'text':safe_text(s,250),'attrs':visible_attrs(s)})
    except Exception:
        form=None
    return form,info

def submit_panel_query(page, panel, input_el, before_hash):
    form,signature=form_signature(input_el,panel)
    evidence={'method':None,'form_signature':signature,'clicked':False}
    roots=[]
    if form is not None: roots.append(('form',form))
    roots.append(('panel',panel))
    for root_name,root in roots:
        for selector in ['button:has-text("Search")','input[type="submit"]','button[type="submit"]']:
            try:
                loc=root.locator(selector)
                for i in range(min(loc.count(),15)):
                    el=loc.nth(i)
                    if not el.is_visible(): continue
                    evidence.update({'method':f'{root_name}:{selector}','clicked':True,'submit_control':{'text':safe_text(el,250),'attrs':visible_attrs(el)}})
                    el.click()
                    return evidence
            except Exception:
                continue
    try:
        input_el.press('Enter')
        evidence.update({'method':'panel_input:Enter','clicked':False})
        return evidence
    except Exception:
        pass
    legacy=submit_query(page,input_el,before_hash)
    evidence.update({'method':'legacy_submit_query_fallback','legacy':legacy})
    return evidence

def result_table_snapshot(page):
    best=None
    try:
        tables=page.locator('table')
        for i in range(min(tables.count(),30)):
            t=tables.nth(i)
            if not t.is_visible(): continue
            headers=[]
            try:
                hs=t.locator('thead th')
                for j in range(min(hs.count(),20)):
                    headers.append(safe_text(hs.nth(j),160))
            except Exception:
                pass
            header_blob=' '.join(headers).lower()
            table_text=safe_text(t,5000)
            semantic=(
              ('serial' in header_blob and 'trademark' in header_blob) or
              ('status' in header_blob and 'registered' in header_blob) or
              ('serial trademark status' in table_text.lower())
            )
            if not semantic: continue
            rows=[]
            try:
                trs=t.locator('tbody tr')
                for j in range(min(trs.count(),25)):
                    tr=trs.nth(j)
                    if not tr.is_visible(): continue
                    txt=safe_text(tr,1200)
                    low=txt.lower()
                    if not txt or 'no data available' in low: continue
                    cells=[]
                    tds=tr.locator('td')
                    for k in range(min(tds.count(),12)):
                        cells.append(safe_text(tds.nth(k),300))
                    links=[]
                    als=tr.locator('a')
                    for k in range(min(als.count(),8)):
                        a=als.nth(k)
                        if a.is_visible():
                            links.append({'text':safe_text(a,220),'href':a.get_attribute('href')})
                    rows.append({'text':txt,'cells':cells,'links':links})
            except Exception:
                pass
            snap={'table_index':i,'headers':headers,'rows':rows[:5],'row_count_observed':len(rows),'table_text_excerpt':table_text[:1800]}
            if best is None or snap['row_count_observed']>best['row_count_observed']:
                best=snap
    except Exception:
        pass
    return best or {'table_index':None,'headers':[],'rows':[],'row_count_observed':0,'table_text_excerpt':''}

def terminal_result_state(page, timeout_seconds=12):
    deadline=time.time()+timeout_seconds
    last=None
    while time.time()<deadline:
        try:
            body=norm(page.locator('body').inner_text(timeout=3000))
        except Exception:
            body=''
        low=body.lower()
        table=result_table_snapshot(page)
        totals=[int(x.replace(',','')) for x in re.findall(r'Showing\s+\d+\s+to\s+\d+\s+of\s+([\d,]+)\s+results',body,re.I)]
        zero=bool(re.search(r'Showing\s+0\s+to\s+0\s+of\s+0\s+results',body,re.I)) or 'no data available in table' in low and any(x==0 for x in totals)
        control=any(x in low for x in ['captcha','verify you are human','are you a robot','human verification'])
        last={'terminal':None,'table':table,'result_totals':totals[:20],'zero_marker':zero,'control_marker':control,'body_excerpt':body[:2200]}
        if control:
            last['terminal']='CONTROL_BLOCKED'; return last
        if table['row_count_observed']>0:
            last['terminal']='POSITIVE_ROWS'; return last
        if zero:
            last['terminal']='ZERO_RESULTSET'; return last
        page.wait_for_timeout(500)
    if last is None:
        last={'terminal':'TIMEOUT','table':result_table_snapshot(page),'result_totals':[],'zero_marker':False,'control_marker':False,'body_excerpt':''}
    else:
        last['terminal']='TIMEOUT'
    return last

def query_binding(input_el, query, page):
    value=None
    try: value=input_el.input_value(timeout=1500)
    except Exception: pass
    body_query=False
    try: body_query=query.lower() in norm(page.locator('body').inner_text(timeout=2500)).lower()
    except Exception: pass
    url_norm=page.url.lower().replace('%20',' ').replace('+',' ')
    return {
      'input_value':value,
      'input_value_matches':(value or '').strip()==query,
      'query_visible_in_page':body_query,
      'query_bound_in_url':query.lower() in url_norm
    }

def tmhunt_mode(browser,mode,query,expect):
    page=browser.new_page(viewport={'width':1440,'height':1000})
    rec={'resolver':'TMHUNT','mode':mode,'query':query,'expect':expect,'state':'MODE_UNPROVEN','failure_signature':None,'harness_revision':HARNESS_REVISION}
    try:
        page.goto('http://www.tmhunt.com/',wait_until='domcontentloaded',timeout=30000)
        page.wait_for_timeout(900)
        rec['query_panel']=open_public_query_panel(page,{'public_query_anchor':'#query','url':'http://www.tmhunt.com/'})
        panel=panel_locator(page)
        rec['mode_control']=click_mode_control(page,panel,mode)
        rec['active_mode_attestation']=attest_active_mode(page,panel,mode)
        selected,inputs=choose_panel_search_input(panel)
        rec['panel_input_candidates']=inputs[:20]
        if not selected:
            rec['failure_signature']='TMHUNT_PANEL_SEARCH_INPUT_NOT_FOUND'; return rec
        input_el,input_desc=selected
        rec['selected_panel_input']=input_desc
        if not rec['active_mode_attestation']['attested']:
            rec['failure_signature']='TMHUNT_ACTIVE_MODE_NOT_ATTESTED'; return rec

        before=sha(page.content())
        input_el.fill(query)
        rec['pre_submit_query_binding']=query_binding(input_el,query,page)
        rec['submission']=submit_panel_query(page,panel,input_el,before)
        terminal=terminal_result_state(page,12)
        rec['terminal_result']=terminal
        rec['final_url']=page.url
        rec['query_binding']=query_binding(input_el,query,page)
        rec['body_sha256']=sha(page.content())
        rec['result_totals']=terminal.get('result_totals',[])
        rec['result_structure']=terminal.get('table',{})
        rec['positive_rows_observed']=terminal.get('table',{}).get('row_count_observed',0)
        rec['zero_marker']=terminal.get('zero_marker',False)

        bound=rec['query_binding']['input_value_matches'] or rec['query_binding']['query_visible_in_page'] or rec['query_binding']['query_bound_in_url'] or rec['pre_submit_query_binding']['input_value_matches']
        if terminal['terminal']=='CONTROL_BLOCKED':
            rec['state']='MODE_BLOCKED'; rec['failure_signature']='TMHUNT_CONTROL_OR_HUMAN_VERIFICATION_OBSERVED'
        elif not bound:
            rec['failure_signature']='TMHUNT_QUERY_BINDING_NOT_ATTESTED_AFTER_SUBMISSION'
        elif expect=='POSITIVE' and terminal['terminal']=='POSITIVE_ROWS' and rec['positive_rows_observed']>0:
            rec['state']='MODE_PASS'
        elif expect=='ZERO' and terminal['terminal']=='ZERO_RESULTSET':
            rec['state']='MODE_PASS'
        else:
            rec['failure_signature']='TMHUNT_NATIVE_RESULTSET_NOT_BOUND_AFTER_CAUSAL_REPAIR'
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
      'schema':'AVER_ACCEPTANCE_RECEIPT','engine_version':ENGINE_VERSION,'harness_revision':HARNESS_REVISION,'mode':'ACCEPTANCE_ONLY','phase':PHASE,
      'authority':{'repository':os.getenv('GITHUB_REPOSITORY','UNKNOWN'),'commit_sha':os.getenv('GITHUB_SHA','UNKNOWN'),'workflow_run_id':os.getenv('GITHUB_RUN_ID','UNKNOWN'),'workflow_run_attempt':os.getenv('GITHUB_RUN_ATTEMPT','UNKNOWN')},
      'browser_executable':executable,'started_at_utc':started,'finished_at_utc':now(),'phase_state':phase,'resolver_states':states,
      'production_tm_decision_authorized':False,'external_side_effects_authorized':False,'daily7_candidate_queries_executed':False,
      'tmhunt_scope_law':'IC025_ONLY','trademarkia_role_law':'BROAD_RECALL_AND_RECORD_DISCOVERY;_OPAQUE_ZERO_SEMANTICS_DOES_NOT_TURN_FUZZY_MULTI_TOKEN_SEARCH_INTO_EXACT_CLEARANCE',
      'causal_repair_scope':'TMHUNT_POSITIVE_MODE_RESULT_BINDING_ONLY;_FIXED_CANARIES_AND_RESOLVERS_UNCHANGED',
      'records':records,
      'repeatability_identity':{'run_id':os.getenv('GITHUB_RUN_ID','UNKNOWN'),'commit_sha':os.getenv('GITHUB_SHA','UNKNOWN')},
      'next_action':'REQUIRE_SECOND_DISTINCT_A4_RUN_WITH_SAME_EXACT_COMMIT_HARNESS_AND_FIXED_CANARIES_BEFORE_PROMOTION_REVIEW' if phase=='A4_PASS' else 'HOLD_FAILED_A4_CAPABILITY_AFTER_THIS_CAUSAL_REPAIR;_DO_NOT_REPEAT_SAME_STRATEGY_OR_EXPAND_QUERY_BREADTH'
    }
    (OUT/'a4-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'phase_state':phase,'resolver_states':states,'record_states':[(r['resolver'],r['mode'],r['state'],r.get('failure_signature')) for r in records]},indent=2))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
