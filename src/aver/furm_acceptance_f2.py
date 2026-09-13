#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path

from aver.resolvers.common import choose_visible_search_input, norm, submit_scoped, wait_for

OUT = Path('artifacts/furm-f2')
OUT.mkdir(parents=True, exist_ok=True)
HOME = 'https://furm.com/'
QUERY = 'FURMA'
EXPECTED_SERIAL = '98682115'


def probe(page):
    body = ''
    try:
        body = norm(page.locator('body').inner_text(timeout=3000))
    except Exception:
        pass
    lower = body.lower()
    control = any(x in lower for x in ('captcha','verify you are human','are you a robot','human verification'))
    serial_seen = EXPECTED_SERIAL in body
    query_seen = QUERY.lower() in lower
    links = []
    try:
        loc = page.locator("a[href*='/trademarks/']")
        for i in range(min(loc.count(), 80)):
            el = loc.nth(i)
            if not el.is_visible():
                continue
            text = norm(el.inner_text(timeout=1200))[:260]
            href = el.get_attribute('href') or ''
            links.append({'text': text, 'href': href})
            if len(links) >= 25:
                break
    except Exception:
        pass
    expected_link = any(EXPECTED_SERIAL in ((x.get('href') or '') + ' ' + (x.get('text') or '')) for x in links)
    terminal = None
    if control:
        terminal = 'CONTROL_BLOCKED'
    elif serial_seen or expected_link:
        terminal = 'KNOWN_POSITIVE_BOUND'
    elif links and query_seen:
        terminal = 'RESULTSET_WITHOUT_EXPECTED_RECORD'
    return {
        'terminal': terminal,
        'serial_seen': serial_seen,
        'expected_record_link_seen': expected_link,
        'query_visible': query_seen,
        'result_links': links,
        'body_excerpt': body[:3000],
    }


def main():
    from playwright.sync_api import sync_playwright
    executable = os.getenv('AVER_BROWSER_EXECUTABLE') or None
    receipt = {
        'schema': 'AVER_FURM_ACCEPTANCE_F2',
        'acceptance_only': True,
        'fixed_canary': {'query': QUERY, 'expected_serial': EXPECTED_SERIAL},
        'daily7_candidate_queries_executed': False,
        'live_gate_authorized': False,
        'external_side_effects_authorized': False,
        'state': 'FURM_F2_UNPROVEN',
    }
    with sync_playwright() as p:
        launch = {'headless': True}
        if executable:
            launch['executable_path'] = executable
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        try:
            page.goto(HOME, wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(900)
            selected, candidates = choose_visible_search_input(page)
            receipt['input_candidates'] = candidates[:10]
            if not selected:
                receipt['failure_signature'] = 'FURM_VISIBLE_SEARCH_INPUT_NOT_FOUND'
            else:
                input_el, desc = selected
                receipt['selected_input'] = desc
                input_el.fill(QUERY)
                page.wait_for_timeout(250)
                receipt['pre_submit_value'] = input_el.input_value(timeout=1500)
                if receipt['pre_submit_value'] != QUERY:
                    receipt['failure_signature'] = 'FURM_QUERY_BINDING_FAILED'
                else:
                    receipt['submission'] = submit_scoped(page, page, input_el)
                    terminal = wait_for(page, lambda: probe(page), timeout_seconds=15)
                    receipt['terminal_result'] = terminal
                    receipt['final_url'] = page.url
                    if terminal.get('terminal') == 'KNOWN_POSITIVE_BOUND':
                        receipt['state'] = 'FURM_F2_KNOWN_POSITIVE_QUERY_PASS'
                    elif terminal.get('terminal') == 'CONTROL_BLOCKED':
                        receipt['failure_signature'] = 'FURM_CONTROL_BLOCKED'
                    else:
                        receipt['failure_signature'] = 'FURM_KNOWN_POSITIVE_NOT_BOUND'
        finally:
            page.close()
            browser.close()

    receipt['next_action'] = 'PROBE_OPAQUE_NATIVE_ZERO_SEMANTICS' if receipt['state'] == 'FURM_F2_KNOWN_POSITIVE_QUERY_PASS' else 'HOLD_FURM_QUERY_CAPABILITY'
    (OUT/'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(receipt['state'])
    print('final_url=', receipt.get('final_url'))
    print('failure_signature=', receipt.get('failure_signature'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
