#!/usr/bin/env python3
import json
import os
from pathlib import Path

from aver.resolvers.common import attrs, safe_text

OUT = Path('artifacts/trademarkia-exact-probe')
OUT.mkdir(parents=True, exist_ok=True)
URL = 'https://www.trademarkia.com/trademark/search'
KEYWORDS = ('exact', 'wordmark', 'field', 'builder', 'match', 'phrase')


def main():
    from playwright.sync_api import sync_playwright
    executable = os.getenv('AVER_BROWSER_EXECUTABLE') or None
    receipt = {
        'schema': 'AVER_TRADEMARKIA_EXACT_CONTROL_PROBE',
        'probe_only': True,
        'candidate_queries_executed': False,
        'new_resolver_added': False,
        'live_gate_authorized': False,
        'controls': [],
        'exact_semantics_proven': False,
    }
    with sync_playwright() as p:
        launch = {'headless': True}
        if executable:
            launch['executable_path'] = executable
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        try:
            page.goto(URL, wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(1200)
            loc = page.locator("button, [role='button'], [role='tab'], [role='combobox'], select, input, label, a")
            for i in range(min(loc.count(), 500)):
                el = loc.nth(i)
                try:
                    if not el.is_visible():
                        continue
                except Exception:
                    continue
                text = safe_text(el, 320)
                at = attrs(el)
                blob = (text + ' ' + json.dumps(at, sort_keys=True)).lower()
                if not any(k in blob for k in KEYWORDS):
                    continue
                receipt['controls'].append({'text': text, 'attrs': at})
                if len(receipt['controls']) >= 80:
                    break
            receipt['control_probe_state'] = 'EXACT_CONTROL_CANDIDATE_DISCOVERED' if receipt['controls'] else 'NO_EXPLICIT_EXACT_CONTROL_DISCOVERED'
        finally:
            page.close()
            browser.close()
    (OUT/'probe.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('AVER_TRADEMARKIA_EXACT_CONTROL_PROBE_COMPLETE')
    print(receipt['control_probe_state'], 'controls=', len(receipt['controls']))
    for c in receipt['controls'][:30]:
        print(c['text'], c['attrs'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
