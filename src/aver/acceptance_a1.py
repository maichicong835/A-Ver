#!/usr/bin/env python3
import hashlib, json, os, re, time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

ENGINE_VERSION='0.1.0'
PHASE='A1_KNOWN_POSITIVE_BINDING'
OUT=Path('artifacts/a1'); OUT.mkdir(parents=True,exist_ok=True)
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 A-Ver-Acceptance/0.1'

class StructureParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.forms=[]; self.scripts=[]; self.current_form=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs); tag=tag.lower()
        if tag=='a' and a.get('href'):
            self.links.append(a.get('href'))
        elif tag=='script' and a.get('src'):
            self.scripts.append(a.get('src'))
        elif tag=='form':
            self.current_form={'method':(a.get('method') or 'GET').upper(),'action':a.get('action') or '','inputs':[]}
            self.forms.append(self.current_form)
        elif tag=='input' and self.current_form is not None:
            self.current_form['inputs'].append({'name':a.get('name'),'type':a.get('type','text'),'value':a.get('value')})
    def handle_endtag(self,tag):
        if tag.lower()=='form': self.current_form=None

def now(): return datetime.now(timezone.utc).isoformat()
def digest(b): return hashlib.sha256(b).hexdigest()

def fetch(url,limit=2_000_000):
    req=Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml,*/*;q=0.8','Accept-Language':'en-US,en;q=0.8'})
    rec={'url':url,'status':None,'final_url':None,'content_type':None,'bytes':0,'sha256':None,'error':None}
    body=b''
    try:
        with build_opener(HTTPRedirectHandler()).open(req,timeout=20) as r:
            body=r.read(limit); rec['status']=getattr(r,'status',None) or r.getcode(); rec['final_url']=r.geturl(); rec['content_type']=r.headers.get('Content-Type')
    except HTTPError as e:
        rec['status']=e.code; rec['final_url']=e.geturl(); rec['error']=f'HTTP_{e.code}'
        try: body=e.read(256000)
        except Exception: pass
    except URLError as e: rec['error']=f'NETWORK_{type(getattr(e,"reason",e)).__name__}:{str(getattr(e,"reason",e))[:160]}'
    except Exception as e: rec['error']=f'{type(e).__name__}:{str(e)[:160]}'
    rec['bytes']=len(body); rec['sha256']=digest(body) if body else None
    return rec,body.decode('utf-8',errors='ignore')

def tmhunt_route_discovery():
    out={'state':'PUBLIC_QUERY_ROUTE_UNRESOLVED','surfaces':[],'route_candidates':[]}
    candidates=[]
    for url in ['http://www.tmhunt.com/','http://www.tmhunt.com/help.php']:
        rec,text=fetch(url); p=StructureParser();
        try: p.feed(text[:1_500_000])
        except Exception: pass
        routes=[]
        for href in p.links:
            h=href.lower()
            if any(k in h for k in ['search','query','mark','trademark','hunt']): routes.append(urljoin(rec['final_url'] or url,href))
        for f in p.forms:
            act=urljoin(rec['final_url'] or url,f['action'] or '')
            if f['inputs'] or 'search' in act.lower(): routes.append(act)
        candidates.extend(routes)
        out['surfaces'].append({'fetch':rec,'form_count':len(p.forms),'link_count':len(p.links),'script_count':len(p.scripts),'route_candidates':sorted(set(routes))[:30]})
    out['route_candidates']=sorted(set(candidates))[:50]
    if out['route_candidates']: out['state']='PUBLIC_QUERY_ROUTE_DISCOVERED'
    return out

def trademarkia_known_positive():
    url='https://www.trademarkia.com/just-do-it-50086105'
    rec,text=fetch(url)
    lower=text.lower()
    checks={
        'mark_text': 'just do it' in lower,
        'serial_number': '50086105' in text,
        'owner': 'nike' in lower,
        'class_016': bool(re.search(r'\b016\b',text)) or 'class 16' in lower or 'class 016' in lower
    }
    state='A1_KNOWN_POSITIVE_BINDING_PASS' if rec['status']==200 and all(checks.values()) else 'A1_KNOWN_POSITIVE_BINDING_INCOMPLETE'
    return {'state':state,'fetch':rec,'checks':checks,'canary':'JUST DO IT / serial 50086105','record_url':url}

def main():
    started=now(); tmh=tmhunt_route_discovery(); tmk=trademarkia_known_positive()
    resolver_states={'TMHUNT':tmh['state'],'TRADEMARKIA':tmk['state']}
    if tmk['state'].endswith('_PASS') and tmh['state']=='PUBLIC_QUERY_ROUTE_DISCOVERED': phase='A1_PARTIAL_ROUTE_READY'
    elif tmk['state'].endswith('_PASS'): phase='A1_PARTIAL_TMHUNT_ROUTE_UNRESOLVED'
    else: phase='A1_BLOCKED_KNOWN_POSITIVE_BINDING'
    receipt={
      'schema':'AVER_ACCEPTANCE_RECEIPT','engine_version':ENGINE_VERSION,'mode':'ACCEPTANCE_ONLY','phase':PHASE,
      'authority':{'repository':os.getenv('GITHUB_REPOSITORY','UNKNOWN'),'commit_sha':os.getenv('GITHUB_SHA','UNKNOWN'),'workflow_run_id':os.getenv('GITHUB_RUN_ID','UNKNOWN'),'workflow_run_attempt':os.getenv('GITHUB_RUN_ATTEMPT','UNKNOWN')},
      'started_at_utc':started,'finished_at_utc':now(),'phase_state':phase,'resolver_states':resolver_states,
      'production_tm_decision_authorized':False,'external_side_effects_authorized':False,'daily7_candidate_queries_executed':False,'negative_clearance_inferred':False,
      'tmhunt':tmh,'trademarkia':tmk,
      'next_action':'USE_ONLY_DISCOVERED_PUBLIC_TMHUNT_ROUTE_FOR_FIXED_KNOWN_POSITIVE_CANARY;_DO_NOT_USE_HIDDEN_ENDPOINTS_OR_DAILY7_PHRASES' if tmh['state']=='PUBLIC_QUERY_ROUTE_DISCOVERED' else 'REPAIR_ONLY_TMHUNT_PUBLIC_QUERY_ROUTE_DISCOVERY_WITH_NORMAL_BROWSER_TRANSPORT'
    }
    p=OUT/'a1-receipt.json'; p.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'phase_state':phase,'resolver_states':resolver_states,'tmhunt_route_candidates':tmh['route_candidates'][:10]},indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
