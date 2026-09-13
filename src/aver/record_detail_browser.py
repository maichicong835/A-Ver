#!/usr/bin/env python3

from .record_details import parse_trademarkia_record_detail
from .resolvers.common import norm, sha


def capture_expanded_trademarkia_record(browser, record_url, max_read_more_clicks=6):
    """Capture a direct Trademarkia record after bounded visible 'Read more' expansion.

    This is a read-only evidence primitive. It does not infer similarity,
    goods-relatedness, or TM outcome and does not bypass controls.
    """
    rec = {
        "record_url": record_url,
        "state": "EXPANDED_RECORD_UNPROVEN",
        "failure_signature": None,
        "read_more_clicks": 0,
    }
    if not isinstance(record_url, str) or not record_url.startswith("https://www.trademarkia.com/"):
        rec["failure_signature"] = "TRADEMARKIA_RECORD_URL_SCOPE_REJECTED"
        return rec

    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    try:
        page.goto(record_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(900)
        body_before = norm(page.locator("body").inner_text(timeout=10000))
        lower_before = body_before.lower()
        if any(x in lower_before for x in ("captcha", "verify you are human", "are you a robot", "human verification")):
            rec["state"] = "EXPANDED_RECORD_BLOCKED"
            rec["failure_signature"] = "TRADEMARKIA_CONTROL_OR_HUMAN_VERIFICATION_OBSERVED"
            return rec

        selectors = [
            "button:has-text('Read more')",
            "a:has-text('Read more')",
            "[role='button']:has-text('Read more')",
        ]
        clicked = 0
        seen = set()
        for selector in selectors:
            try:
                loc = page.locator(selector)
                for i in range(min(loc.count(), max_read_more_clicks)):
                    if clicked >= max_read_more_clicks:
                        break
                    el = loc.nth(i)
                    try:
                        if not el.is_visible():
                            continue
                        key = (selector, i, (el.inner_text() or "").strip())
                        if key in seen:
                            continue
                        seen.add(key)
                        el.click()
                        clicked += 1
                        page.wait_for_timeout(250)
                    except Exception:
                        continue
            except Exception:
                continue

        body_after = norm(page.locator("body").inner_text(timeout=10000))
        structured = parse_trademarkia_record_detail(body_after)
        rec.update({
            "read_more_clicks": clicked,
            "body_length_before": len(body_before),
            "body_length_after": len(body_after),
            "body_sha256": sha(page.content()),
            "structured_record_detail": structured,
            "final_url": page.url,
        })
        if structured.get("structured_detail_complete"):
            rec["state"] = "EXPANDED_RECORD_PASS"
        else:
            rec["failure_signature"] = "TRADEMARKIA_EXPANDED_RECORD_DETAIL_INCOMPLETE"
    except Exception as exc:
        rec["state"] = "EXPANDED_RECORD_BLOCKED"
        rec["failure_signature"] = f"{type(exc).__name__}:{str(exc)[:220]}"
    finally:
        page.close()
    return rec
