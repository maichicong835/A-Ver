#!/usr/bin/env python3
import re

from .common import choose_visible_search_input, norm, safe_text, sha, submit_scoped, wait_for


class TrademarkiaResolver:
    """Broad-recall public-browser resolver for Trademarkia.

    The resolver deliberately distinguishes fuzzy/broad positive discovery from
    opaque single-token zero semantics. It does not infer exact multi-token
    negative clearance from an opaque zero canary.
    """

    SEARCH_URL = "https://www.trademarkia.com/trademark/search"
    KNOWN_RECORD_URL = "https://www.trademarkia.com/just-do-it-50086105"

    def __init__(self, browser):
        self.browser = browser

    def _search_probe(self, page, query, expected_identifier=None):
        body = ""
        try:
            body = norm(page.locator("body").inner_text(timeout=3000))
        except Exception:
            pass
        lower = body.lower()
        count_match = re.search(r"([\d,]+)\s+trademarks?\s+found\s+for", body, re.I)
        total = int(count_match.group(1).replace(",", "")) if count_match else None
        no_results = "no results" in lower
        identifier_seen = expected_identifier in body if expected_identifier else False
        query_visible = query.lower() in lower
        url_blob = page.url.lower().replace("%20", " ").replace("+", " ")
        query_in_url = query.lower() in url_blob
        control = any(x in lower for x in ("captcha", "verify you are human", "are you a robot", "human verification"))
        links = []
        try:
            loc = page.locator("a[href*='/trademark'], a[href*='trademarkia.com/']")
            for i in range(min(loc.count(), 30)):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                text = safe_text(el, 260)
                href = el.get_attribute("href")
                if text or href:
                    links.append({"text": text, "href": href})
        except Exception:
            pass
        result = {
            "terminal": None,
            "reported_total": total,
            "no_results_marker": no_results,
            "expected_identifier_seen": identifier_seen,
            "query_visible": query_visible,
            "query_bound_in_url": query_in_url,
            "result_link_samples": links[:8],
            "body_excerpt": body[:2200],
        }
        if control:
            result["terminal"] = "CONTROL_BLOCKED"
        elif no_results:
            result["terminal"] = "ZERO_RESULTSET"
        elif identifier_seen or (total is not None and total > 0):
            result["terminal"] = "POSITIVE_RESULTSET"
        return result

    def search(self, query, expected_kind, expected_identifier=None):
        page = self.browser.new_page(viewport={"width": 1440, "height": 1000})
        rec = {"resolver": "TRADEMARKIA", "mode": expected_kind, "query": query, "state": "CAPABILITY_UNPROVEN", "failure_signature": None}
        try:
            page.goto(self.SEARCH_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(900)
            selected, candidates = choose_visible_search_input(page)
            rec["input_candidates"] = candidates[:20]
            if not selected:
                rec["failure_signature"] = "TRADEMARKIA_VISIBLE_SEARCH_INPUT_NOT_FOUND"
                return rec
            input_el, input_desc = selected
            rec["selected_input"] = input_desc
            input_el.fill(query)
            rec["pre_submit_input_value"] = input_el.input_value(timeout=1500)
            rec["submission"] = submit_scoped(page, page, input_el)
            terminal = wait_for(page, lambda: self._search_probe(page, query, expected_identifier), timeout_seconds=16)
            rec["terminal_result"] = terminal
            rec["final_url"] = page.url
            rec["body_sha256"] = sha(page.content())
            if terminal.get("terminal") == "CONTROL_BLOCKED":
                rec["state"] = "CAPABILITY_BLOCKED"
                rec["failure_signature"] = "TRADEMARKIA_CONTROL_OR_HUMAN_VERIFICATION_OBSERVED"
            elif expected_kind in ("KNOWN_POSITIVE", "FUZZY_RECALL") and terminal.get("terminal") == "POSITIVE_RESULTSET":
                rec["state"] = "CAPABILITY_PASS"
            elif expected_kind == "OPAQUE_ZERO" and terminal.get("terminal") == "ZERO_RESULTSET":
                rec["state"] = "CAPABILITY_PASS"
            else:
                rec["failure_signature"] = "TRADEMARKIA_DECLARED_CAPABILITY_SEMANTICS_NOT_BOUND"
        except Exception as exc:
            rec["state"] = "CAPABILITY_BLOCKED"
            rec["failure_signature"] = f"{type(exc).__name__}:{str(exc)[:220]}"
        finally:
            page.close()
        return rec

    def bind_known_record(self, expected_serial="50086105"):
        page = self.browser.new_page(viewport={"width": 1440, "height": 1000})
        rec = {"resolver": "TRADEMARKIA", "mode": "KNOWN_RECORD_BINDING", "record_url": self.KNOWN_RECORD_URL, "expected_serial": expected_serial, "state": "CAPABILITY_UNPROVEN", "failure_signature": None}
        try:
            page.goto(self.KNOWN_RECORD_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(900)
            body = norm(page.locator("body").inner_text(timeout=10000))
            lower = body.lower()
            serial_seen = expected_serial in body
            context_seen = any(token in lower for token in ("live", "pending", "registered")) and any(token in lower for token in ("class 016", "class 16", "paper goods", "printed"))
            control = any(x in lower for x in ("captcha", "verify you are human", "are you a robot", "human verification"))
            rec.update({"serial_seen": serial_seen, "status_or_class_context_seen": context_seen, "body_sha256": sha(page.content()), "body_excerpt": body[:2200]})
            if control:
                rec["state"] = "CAPABILITY_BLOCKED"
                rec["failure_signature"] = "TRADEMARKIA_CONTROL_OR_HUMAN_VERIFICATION_OBSERVED"
            elif serial_seen and context_seen:
                rec["state"] = "CAPABILITY_PASS"
            else:
                rec["failure_signature"] = "TRADEMARKIA_KNOWN_RECORD_FIELDS_NOT_BOUND"
        except Exception as exc:
            rec["state"] = "CAPABILITY_BLOCKED"
            rec["failure_signature"] = f"{type(exc).__name__}:{str(exc)[:220]}"
        finally:
            page.close()
        return rec
