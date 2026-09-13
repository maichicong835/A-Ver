#!/usr/bin/env python3
import json, os, re
from pathlib import Path
from playwright.sync_api import sync_playwright

URL='https://www.trademarkia.com/trademark/search'
CASES=[
 {'name':'KNOWN_POSITIVE_MULTIWORD','query':'JUST DO IT','expected':'POSITIVE'},
 {'name':'OPAQUE_MULTIWORD_ZERO','query':'QZXJ VMRK PLN 91372','expected':'ZERO'},
]


def body(page):
    try: return re.sub(r'\s+',' ',page.locator('body').inner_text(timeout=5000)).strip()
    except Exception: return ''


def visible_controls(page):
    out=[]
    for selector in ['button','[role="button"]','[role="option"]','label','select','input']:
        try:
            loc=page.locator(selector)
            for i in range(min(loc.count(),80)):
                el=loc.nth(i)
                if not el.is_visible(): continue
                txt=(el.inner_text() or '').strip() if selector!='input' else ''
                out.append({'selector':selector,'index':i,'text':txt[:160],'placeholder':el.get_attribute('placeholder') or '', 'aria_label':el.get_attribute('aria-label') or '', 'value':el.get_attribute('value') or ''})
        except Exception: pass
    return out


def choose_search(page):
    for sel in ['input[placeholder*="search" i]','input[aria-label*="search" i]','input[type="search"]','input[type="text"]']:
        try:
            loc=page.locator(sel)
            for i in range(min(loc.count(),20)):
                el=loc.nth(i)
                if el.is_visible(): return el, {'selector':sel,'index':i,'placeholder':el.get_attribute('placeholder') or '', 'aria_label':el.get_attribute('aria-label') or ''}
        except Exception: pass
    return None,None


def bind_exact_mode(page):
    observations=visible_controls(page)
    patterns=['exact match','exact phrase','exact']
    # Prefer semantically explicit visible controls only. Do not infer exactness from quoted input.
    for pattern in patterns:
        for sel in [f'button:has-text("{pattern}")', f'[role="option"]:has-text("{pattern}")', f'label:has-text("{pattern}")']:
            try:
                loc=page.locator(sel)
                for i in range(min(loc.count(),10)):
                    el=loc.nth(i)
                    if not el.is_visible(): continue
                    txt=(el.inner_text() or '').strip()
                    if pattern=='exact' and txt.lower()!='exact':
                        continue
                    try: el.click(); page.wait_for_timeout(350)
                    except Exception: continue
                    post=body(page).lower()
                    return {'bound':True,'method':sel,'control_text':txt,'post_body_has_exact': 'exact' in post, 'observations':observations[:80]}
            except Exception: pass
    return {'bound':False,'failure_signature':'TRADEMARKIA_EXACT_MODE_NOT_MACHINE_BOUND','observations':observations[:80]}


def probe(page, query):
    b=body(page); lo=b.lower()
    m=re.search(r'([\d,]+)\s+trademarks?\s+found\s+for',b,re.I)
    count=int(m.group(1).replace(',','')) if m else None
    zero='no results' in lo or '0 trademarks found' in lo
    control=any(x in lo for x in ['captcha','verify you are human','are you a robot','human verification'])
    return {'reported_total':count,'positive':count is not None and count>0,'native_zero':zero,'control_blocked':control,'query_visible':query.lower() in lo,'final_url':page.url,'body_excerpt':b[:3500]}


def run_case(browser, case):
    page=browser.new_page(viewport={'width':1440,'height':1000})
    rec={**case,'state':'UNPROVEN','failure_signature':None}
    try:
        page.goto(URL,wait_until='domcontentloaded',timeout=30000); page.wait_for_timeout(1200)
        rec['exact_mode']=bind_exact_mode(page)
        if not rec['exact_mode'].get('bound'):
            rec['failure_signature']=rec['exact_mode']['failure_signature']; return rec
        inp,desc=choose_search(page); rec['selected_input']=desc
        if inp is None:
            rec['failure_signature']='TRADEMARKIA_SEARCH_INPUT_NOT_FOUND'; return rec
        inp.fill(case['query']); page.wait_for_timeout(250); v1=inp.input_value(); page.wait_for_timeout(450); v2=inp.input_value()
        rec['pre_submit_value_1']=v1; rec['pre_submit_value_2']=v2
        if v1!=case['query'] or v2!=case['query']:
            rec['failure_signature']='TRADEMARKIA_EXACT_QUERY_BINDING_UNSTABLE'; return rec
        inp.press('Enter')
        terminal=None
        for _ in range(45):
            page.wait_for_timeout(350); p=probe(page,case['query'])
            if p['control_blocked'] or p['positive'] or p['native_zero']:
                terminal=p; break
        rec['terminal']=terminal or probe(page,case['query'])
        if rec['terminal']['control_blocked']:
            rec['failure_signature']='TRADEMARKIA_CONTROL_BLOCKED'
        elif case['expected']=='POSITIVE' and rec['terminal']['positive']:
            rec['state']='PASS'
        elif case['expected']=='ZERO' and rec['terminal']['native_zero']:
            rec['state']='PASS'
        else:
            rec['failure_signature']='TRADEMARKIA_EXACT_NATIVE_RESULTSET_SEMANTICS_NOT_BOUND'
    except Exception as exc:
        rec['failure_signature']=f'{type(exc).__name__}:{str(exc)[:220]}'
    finally:
        page.close()
    return rec


def main():
    out={'schema':'AVER_TRADEMARKIA_EXACT_CANARY','fixed_canaries_only':True,'daily7_candidate_queries_executed':False,'tm_decision_authorized':False,'phase_state':'TRADEMARKIA_EXACT_CAPABILITY_HOLD','cases':[]}
    executable=os.getenv('AVER_BROWSER_EXECUTABLE') or None
    with sync_playwright() as p:
        launch={'headless':True}
        if executable: launch['executable_path']=executable
        browser=p.chromium.launch(**launch)
        for c in CASES: out['cases'].append(run_case(browser,c))
        browser.close()
    if all(c['state']=='PASS' for c in out['cases']): out['phase_state']='TRADEMARKIA_EXACT_MULTIWORD_SEMANTICS_PASS'
    path=Path('artifacts/trademarkia-exact'); path.mkdir(parents=True,exist_ok=True)
    (path/'receipt.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print('phase_state=',out['phase_state'])
    for c in out['cases']: print(c['name'],c['state'],c.get('failure_signature'),(c.get('terminal') or {}).get('reported_total'))
    # Workflow stays green for HOLD; semantic state is authoritative.

if __name__=='__main__': main()
