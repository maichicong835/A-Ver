#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

from aver.resolvers.common import attrs, choose_visible_search_input, safe_text

OUT = Path('artifacts/furm-f0-f1')
OUT.mkdir(parents=True, exist_ok=True)
HOME = 'https://furm.com/'
KNOWN = 'https://furm.com/trademarks/25-98920101'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 A-Ver-Furm-Acceptance/0.1'


def fetch(url, limit=1_500_000):
    rec = {'url': url, 'status': None, 'final_url': None, 'bytes': 0, 'sha256': None, 'error': None}
    body = b''
    try:
        req = Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8'})
        with build_opener(HTTPRedirectHandler()).open(req, timeout=20) as r:
            body = r.read(limit)
            rec['status'] = getattr(r, 'status', None) or r.getcode()
            rec['final_url'] = r.geturl()
    except HTTPError as exc:
        rec['status'] = exc.code
        rec['final_url'] = exc.geturl()
        rec['error'] = f'HTTP_{exc.code}'
    except URLError as exc:
        rec['error'] = f'NETWORK_{type(getattr(exc, "reason", exc)).__name__}:{str(getattr(exc, "reason", exc))[:180]}'
    except Exception as exc:
        rec['error'] = f'{type(exc).__name__}:{str(exc)[:180]}'
    rec['bytes'] = len(body)
    rec['sha256'] = hashlib.sha256(body).hexdigest() if body else None
    return rec, body.decode('utf-8', errors='ignore')


def main():
    home_fetch, home_html = fetch(HOME)
    record_fetch, record_html = fetch(KNOWN)
    record_lower = record_html.lower()
    known_checks = {
        'serial_98920101': '98920101' in record_html,
        'class_016': ('international class' in record_lower and '016' in record_html) or 'class 016' in record_lower,
        'status_context': any(x in record_lower for x in ('active', 'registered', 'pending', 'published')),
        'goods_services_label': 'goods and services' in record_lower,
    }

    receipt = {
        'schema': 'AVER_FURM_ACCEPTANCE_F0_F1',
        'acceptance_only': True,
        'candidate_queries_executed': False,
        'daily7_live_gate_authorized': False,
        'external_side_effects_authorized': False,
        'transport': {'home': home_fetch, 'known_record': record_fetch},
        'known_record': {'url': KNOWN, 'checks': known_checks},
        'ui_probe': {'search_input': None, 'candidate_controls': []},
    }

    from playwright.sync_api import sync_playwright
    executable = os.getenv('AVER_BROWSER_EXECUTABLE') or None
    with sync_playwright() as p:
        launch = {'headless': True}
        if executable:
            launch['executable_path'] = executable
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        try:
            page.goto(HOME, wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(1000)
            selected, candidates = choose_visible_search_input(page)
            receipt['ui_probe']['input_candidates'] = candidates[:20]
            if selected:
                _, desc = selected
                receipt['ui_probe']['search_input'] = desc
            loc = page.locator("button, [role='button'], [role='tab'], [role='combobox'], select, input, label, a")
            for i in range(min(loc.count(), 350)):
                el = loc.nth(i)
                try:
                    if not el.is_visible():
                        continue
                except Exception:
                    continue
                text = safe_text(el, 120)
                at = attrs(el)
                blob = (text + ' ' + json.dumps(at, sort_keys=True)).lower()
                if any(k in blob for k in ('search', 'class', 'status', 'exact', 'trademark')):
                    receipt['ui_probe']['candidate_controls'].append({'text': text, 'attrs': at})
                    if len(receipt['ui_probe']['candidate_controls']) >= 60:
                        break
        finally:
            page.close()
            browser.close()

    transport_pass = home_fetch['status'] == 200 and record_fetch['status'] == 200
    record_pass = all(known_checks.values())
    search_surface_bound = receipt['ui_probe']['search_input'] is not None
    receipt['phase_state'] = 'FURM_F0_F1_PASS' if transport_pass and record_pass and search_surface_bound else 'FURM_F0_F1_PARTIAL'
    receipt['next_action'] = 'PROBE_FIXED_KNOWN_POSITIVE_QUERY_SEMANTICS_ONLY' if receipt['phase_state'] == 'FURM_F0_F1_PASS' else 'HOLD_FURM_CAPABILITY_NO_QUERY_EXECUTION'
    (OUT/'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(receipt['phase_state'])
    print('transport_pass=', transport_pass, 'record_pass=', record_pass, 'search_surface_bound=', search_surface_bound)
    print('search_input=', receipt['ui_probe']['search_input'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
