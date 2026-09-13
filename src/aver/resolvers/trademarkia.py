#!/usr/bin/env python3
import re

from .common import choose_visible_search_input, norm, safe_text, sha, submit_scoped, wait_for


class TrademarkiaResolver:
    """Broad-recall public-browser resolver for Trademarkia."""

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
        result = {"terminal": None,"reported_total": total,"no_results_marker": no_results,"expected_identifier_seen": identifier_seen,"query_visible": query_visible,"query_bound_in_url": query_in_url,"result_link_samples": links[:8],"body_excerpt": body[:2200]}
        if control:
            result["terminal"] = "CONTROL_BLOCKED"
        elif no_results:
            result["terminal"] = "ZERO_RESULTSET"
        elif identifier_seen or (total is not None and total > 0):
            result["terminal"] = "POSITIVE_RESULTSET"
        return result

    def _bind_query_stably(self, page, query, max_attempts=3):
        attempts = []
        latest_candidates = []
        for attempt in range(1, max_attempts + 1):
            selected, candidates = choose_visible_search_input(page)
            latest_candidates = candidates[:20]
            if not selected:
                attempts.append({"attempt": attempt, "method": None, "value_after_250ms": None, "value_after_700ms": None, "bound": False, "reason": "VISIBLE_SEARCH_INPUT_NOT_FOUND"})
                page.wait_for_timeout(300)
                continue
            input_el, input_desc = selected
            method = "fill" if attempt == 1 else "click_selectall_type"
            try:
                if method == "fill": input_el.fill(query)
                else:
                    input_el.click(); input_el.press("Control+A"); input_el.type(query, delay=20)
                page.wait_for_timeout(250)
                value1 = input_el.input_value(timeout=1500)
                page.wait_for_timeout(450)
                value2 = input_el.input_value(timeout=1500)
                bound = value1 == query and value2 == query
                attempts.append({"attempt": attempt,"method": method,"selected_input": input_desc,"value_after_250ms": value1,"value_after_700ms": value2,"bound": bound})
                if bound: return input_el, input_desc, latest_candidates, {"bound": True, "attempts": attempts, "max_attempts": max_attempts}
            except Exception as exc:
                attempts.append({"attempt": attempt,"method": method,"selected_input": input_desc,"bound": False,"exception": f"{type(exc).__name__}:{str(exc)[:180]}"})
            page.wait_for_timeout(300)
        return None, None, latest_candidates, {"bound": False, "attempts": attempts, "max_attempts": max_attempts}

    def search(self, query, expected_kind, expected_identifier=None, post_terminal_observer=None):
        page = self.browser.new_page(viewport={"width": 1440, "height": 1000})
        rec = {"resolver": "TRADEMARKIA", "mode": expected_kind, "query": query, "state": "CAPABILITY_UNPROVEN", "failure_signature": None}
        try:
            page.goto(self.SEARCH_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(900)
            input_el, input_desc, candidates, binding = self._bind_query_stably(page, query)
            rec["input_candidates"] = candidates; rec["query_binding_attestation"] = binding
            if input_el is None or not binding.get("bound"):
                rec["failure_signature"] = "TRADEMARKIA_QUERY_BINDING_UNSTABLE_BEFORE_SUBMIT"; return rec
            rec["selected_input"] = input_desc; rec["pre_submit_input_value"] = input_el.input_value(timeout=1500)
            if rec["pre_submit_input_value"] != query:
                rec["failure_signature"] = "TRADEMARKIA_QUERY_BINDING_LOST_IMMEDIATELY_BEFORE_SUBMIT"; return rec
            rec["submission"] = submit_scoped(page, page, input_el)
            terminal = wait_for(page, lambda: self._search_probe(page, query, expected_identifier), timeout_seconds=16)
            rec["terminal_result"] = terminal
            if post_terminal_observer is not None and terminal.get("terminal") == "POSITIVE_RESULTSET":
                try:
                    rec["post_terminal_observation"] = post_terminal_observer(page, terminal); rec["post_terminal_observer_state"] = "OBSERVED"
                except Exception as exc:
                    rec["post_terminal_observation"] = None; rec["post_terminal_observer_state"] = "OBSERVER_ERROR"; rec["post_terminal_observer_error"] = f"{type(exc).__name__}:{str(exc)[:220]}"
            rec["final_url"] = page.url; rec["body_sha256"] = sha(page.content())
            if terminal.get("terminal") == "CONTROL_BLOCKED": rec["state"] = "CAPABILITY_BLOCKED"; rec["failure_signature"] = "TRADEMARKIA_CONTROL_OR_HUMAN_VERIFICATION_OBSERVED"
            elif expected_kind in ("KNOWN_POSITIVE", "FUZZY_RECALL") and terminal.get("terminal") == "POSITIVE_RESULTSET": rec["state"] = "CAPABILITY_PASS"
            elif expected_kind == "OPAQUE_ZERO" and terminal.get("terminal") == "ZERO_RESULTSET": rec["state"] = "CAPABILITY_PASS"
            else: rec["failure_signature"] = "TRADEMARKIA_DECLARED_CAPABILITY_SEMANTICS_NOT_BOUND"
        except Exception as exc:
            rec["state"] = "CAPABILITY_BLOCKED"; rec["failure_signature"] = f"{type(exc).__name__}:{str(exc)[:220]}"
        finally:
            page.close()
        return rec

    def bind_record_url(self, record_url, expected_serial, expected_mark=None, expected_class=None):
        rec = {"resolver":"TRADEMARKIA","mode":"DIRECT_RECORD_BINDING","record_url":record_url,"expected_serial":str(expected_serial),"expected_mark":expected_mark,"expected_class":expected_class,"state":"CAPABILITY_UNPROVEN","failure_signature":None}
        if not isinstance(record_url, str) or not record_url.startswith("https://www.trademarkia.com/"):
            rec["failure_signature"] = "TRADEMARKIA_RECORD_URL_SCOPE_REJECTED"; return rec
        if not re.search(r"-" + re.escape(str(expected_serial)) + r"(?:[/?#]|$)", record_url):
            rec["failure_signature"] = "TRADEMARKIA_RECORD_URL_SERIAL_MISMATCH"; return rec
        page = self.browser.new_page(viewport={"width":1440,"height":1000})
        try:
            page.goto(record_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(900)
            body = norm(page.locator("body").inner_text(timeout=10000))
            lower = body.lower()
            control = any(x in lower for x in ("captcha", "verify you are human", "are you a robot", "human verification"))
            serial_seen = str(expected_serial) in body
            mark_seen = True if not expected_mark else expected_mark.lower() in lower
            status_match = re.search(r"\b(Live/(?:Registered|Pending)|Dead/(?:Cancelled|Abandoned)|Registered|Pending)\b", body, re.I)
            classes=[]
            for raw in re.findall(r"\bClass\s+0*(\d{1,3})\b", body, re.I):
                value=str(int(raw)).zfill(3)
                if value not in classes: classes.append(value)
            expected_class_seen = True if not expected_class else str(expected_class).zfill(3) in classes
            rec.update({"serial_seen":serial_seen,"mark_seen":mark_seen,"status":status_match.group(0) if status_match else None,"classes":classes,"expected_class_seen":expected_class_seen,"body_sha256":sha(page.content()),"body_excerpt":body[:5000],"final_url":page.url})
            if control:
                rec["state"]="CAPABILITY_BLOCKED"; rec["failure_signature"]="TRADEMARKIA_CONTROL_OR_HUMAN_VERIFICATION_OBSERVED"
            elif serial_seen and mark_seen and status_match and expected_class_seen:
                rec["state"]="CAPABILITY_PASS"
            else:
                rec["failure_signature"]="TRADEMARKIA_DIRECT_RECORD_FIELDS_NOT_BOUND"
        except Exception as exc:
            rec["state"]="CAPABILITY_BLOCKED"; rec["failure_signature"]=f"{type(exc).__name__}:{str(exc)[:220]}"
        finally:
            page.close()
        return rec

    def bind_known_record(self, expected_serial="50086105"):
        page = self.browser.new_page(viewport={"width": 1440, "height": 1000})
        rec = {"resolver": "TRADEMARKIA", "mode": "KNOWN_RECORD_BINDING", "record_url": self.KNOWN_RECORD_URL, "expected_serial": expected_serial, "state": "CAPABILITY_UNPROVEN", "failure_signature": None}
        try:
            page.goto(self.KNOWN_RECORD_URL, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(900)
            body = norm(page.locator("body").inner_text(timeout=10000)); lower = body.lower()
            serial_seen = expected_serial in body
            context_seen = any(token in lower for token in ("live", "pending", "registered")) and any(token in lower for token in ("class 016", "class 16", "paper goods", "printed"))
            control = any(x in lower for x in ("captcha", "verify you are human", "are you a robot", "human verification"))
            rec.update({"serial_seen": serial_seen, "status_or_class_context_seen": context_seen, "body_sha256": sha(page.content()), "body_excerpt": body[:2200]})
            if control: rec["state"] = "CAPABILITY_BLOCKED"; rec["failure_signature"] = "TRADEMARKIA_CONTROL_OR_HUMAN_VERIFICATION_OBSERVED"
            elif serial_seen and context_seen: rec["state"] = "CAPABILITY_PASS"
            else: rec["failure_signature"] = "TRADEMARKIA_KNOWN_RECORD_FIELDS_NOT_BOUND"
        except Exception as exc:
            rec["state"] = "CAPABILITY_BLOCKED"; rec["failure_signature"] = f"{type(exc).__name__}:{str(exc)[:220]}"
        finally:
            page.close()
        return rec
