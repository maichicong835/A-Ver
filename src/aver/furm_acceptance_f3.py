#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path

from aver.resolvers.common import choose_visible_search_input, norm, submit_scoped, wait_for

OUT = Path('artifacts/furm-f3')
OUT.mkdir(parents=True, exist_ok=True)
HOME = 'https://furm.com/'
QUERY = 'QZXJVMRKPLN91372'

ZERO_PATTERNS = [
    r'no\s+trademarks?\s+found',
    r'no\s+results?\s+found',
    r'0\s+results?',
    r'no\s+matching\s+trademarks?',
]


def probe(page):
    body = ''
    try:
        body = norm(page.locator('body').inner_text(timeout=3000))
    except Exception:
        pass
    lower = body.lower()
    control = any(x in lower for x in ('captcha','verify you are human','are you a robot','human verification'))
    zero_hits = [p for p in ZERO_PATTERNS if re.search(p, body, re.I)]
    result_record_links = []
    try:
        loc = page.locator("a[href*='/trademarks/']")
        for i in range(min(loc.count(), 120)):
            el = loc.nth(i)
            if not el.is_visible():
                continue
            href = el.get_attribute('href') or ''
            text = norm(el.inner_text(timeout=1200))[:240]
            if re.search(r'/trademarks/[^/?#]+-\d{8}(?:$|[?#])', href):
                result_record_links.append({'text': text, 'href': href})
                if len(result_record_links) >= 30:
                    break
    except Exception:
        pass
    query_seen = QUERY.lower() in lower or QUERY.lower() in page.url.lower()
    terminal = None
    if control:
        terminal = 'CONTROL_BLOCKED'
    elif zero_hits and not result_record_links and query_seen:
        terminal = 'ZERO_RESULTSET'
    elif result_record_links and query_seen:
        terminal = 'POSITIVE_RESULTSET'
    return {
        'terminal': terminal,
        'zero_patterns_matched': zero_hits,
        'result_record_links': result_record_links,
        'query_bound_in_result_surface': query_seen,
        'body_excerpt': body[:2800],
    }


def main():
    from playwright.sync_api import sync_playwright
    executable = os.getenv('AVER_BROWSER_EXECUTABLE') or None
    receipt = {
        'schema': 'AVER_FURM_ACCEPTANCE_F3',
        'acceptance_only': True,
        'fixed_canary': {'query': QUERY, 'kind': 'OPAQUE_SINGLE_TOKEN'},
        'daily7_candidate_queries_executed': False,
        'live_gate_authorized': False,
        'state': 'FURM_F3_ZERO_UNPROVEN',
    }
    with sync_playwright() as p:
        launch = {'headless': True}
        if executable:
            launch['executable_path'] = executable
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        try:
            page.goto(HOME, wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(800)
            selected, _ = choose_visible_search_input(page)
            if not selected:
                receipt['failure_signature'] = 'FURM_VISIBLE_SEARCH_INPUT_NOT_FOUND'
            else:
                input_el, desc = selected
                receipt['selected_input'] = desc
                input_el.fill(QUERY)
                receipt['pre_submit_value'] = input_el.input_value(timeout=1500)
                if receipt['pre_submit_value'] != QUERY:
                    receipt['failure_signature'] = 'FURM_QUERY_BINDING_FAILED'
                else:
                    receipt['submission'] = submit_scoped(page, page, input_el)
                    terminal = wait_for(page, lambda: probe(page), timeout_seconds=15)
                    receipt['terminal_result'] = terminal
                    receipt['final_url'] = page.url
                    if terminal.get('terminal') == 'ZERO_RESULTSET':
                        receipt['state'] = 'FURM_F3_OPAQUE_ZERO_PASS'
                    elif terminal.get('terminal') == 'CONTROL_BLOCKED':
                        receipt['failure_signature'] = 'FURM_CONTROL_BLOCKED'
                    else:
                        receipt['failure_signature'] = 'FURM_NATIVE_ZERO_NOT_BOUND'
        finally:
            page.close()
            browser.close()

    receipt['negative_semantics_scope'] = 'OPAQUE_SINGLE_TOKEN_ONLY' if receipt['state'] == 'FURM_F3_OPAQUE_ZERO_PASS' else 'NONE'
    receipt['multi_token_exact_negative_proven'] = False
    receipt['next_action'] = 'PROBE_MULTI_TOKEN_MATCHING_BEHAVIOR_WITH_FIXED_CANARIES' if receipt['state'] == 'FURM_F3_OPAQUE_ZERO_PASS' else 'HOLD_FURM_NEGATIVE_CAPABILITY'
    (OUT/'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(receipt['state'])
    print('negative_semantics_scope=', receipt['negative_semantics_scope'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
