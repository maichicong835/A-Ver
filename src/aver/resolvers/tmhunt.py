#!/usr/bin/env python3
import json
import re

from .common import attrs, choose_visible_search_input, compact_json, norm, safe_text, sha, submit_scoped, wait_for


class TMHuntResolver:
    """Public-browser resolver for the machine-proven TMHunt capability profile.

    Declared production candidate scope is IC025 with Exact and Partial modes
    only. Split/Wildcard are intentionally absent: unproven modes must not be
    retried or counted as coverage.
    """

    URL = "http://www.tmhunt.com/"
    SCOPE = "IC025"
    ACCEPTED_MODES = ("EXACT", "PARTIAL")
    LABELS = {"EXACT": "Exact Match", "PARTIAL": "Partial Match"}

    def __init__(self, browser):
        self.browser = browser

    def _open_panel(self, page):
        page.goto(self.URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(800)
        panel = page.locator("#query")
        try:
            if panel.count() and panel.first.is_visible():
                return panel.first, {"opened": True, "method": "already_visible"}
        except Exception:
            pass
        for selector in ["a[href='#query']", "button:has-text('Query')", "a:has-text('Query')"]:
            try:
                loc = page.locator(selector)
                for i in range(min(loc.count(), 15)):
                    el = loc.nth(i)
                    if not el.is_visible():
                        continue
                    el.click()
                    page.wait_for_timeout(500)
                    if panel.count() and panel.first.is_visible():
                        return panel.first, {"opened": True, "method": selector}
            except Exception:
                continue
        return page.locator("body"), {"opened": False, "method": None}

    def _select_mode(self, page, panel, mode):
        if mode not in self.ACCEPTED_MODES:
            raise ValueError(f"TMHUNT_MODE_NOT_IN_DECLARED_PROFILE:{mode}")
        target = self.LABELS[mode]
        evidence = {"target": target, "clicked": False, "method": None}
        for root_name, root in [("panel", panel), ("page", page)]:
            for selector in [
                f"label:has-text('{target}')",
                f"button:has-text('{target}')",
                f"a:has-text('{target}')",
                f"[role='tab']:has-text('{target}')",
                f"text='{target}'",
            ]:
                try:
                    loc = root.locator(selector)
                    for i in range(min(loc.count(), 20)):
                        el = loc.nth(i)
                        if not el.is_visible():
                            continue
                        evidence["element"] = {"text": safe_text(el, 300), "attrs": attrs(el)}
                        el.click()
                        page.wait_for_timeout(400)
                        evidence.update({"clicked": True, "method": f"{root_name}:{selector}"})
                        return evidence
                except Exception:
                    continue
        return evidence

    def _attest_mode(self, panel, mode):
        target = self.LABELS[mode]
        token = mode.lower()
        snapshots = []
        for selector in ["input:checked", "[aria-selected='true']", "[aria-pressed='true']", "[aria-checked='true']", ".active", ".selected", "option:checked"]:
            try:
                loc = panel.locator(selector)
                for i in range(min(loc.count(), 40)):
                    el = loc.nth(i)
                    if not el.is_visible() and selector not in ("input:checked", "option:checked"):
                        continue
                    item = {"selector": selector, "text": safe_text(el, 400), "attrs": attrs(el)}
                    try:
                        if selector == "input:checked":
                            eid = el.get_attribute("id")
                            if eid:
                                label = panel.locator(f"label[for='{eid}']")
                                if label.count():
                                    item["label_text"] = safe_text(label.first, 300)
                        item["parent_text"] = safe_text(el.locator("xpath=.."), 500)
                    except Exception:
                        pass
                    snapshots.append(item)
            except Exception:
                continue
        matches = [x for x in snapshots if token in compact_json(x).lower() or target.lower() in compact_json(x).lower()]
        return {"attested": bool(matches), "target": target, "matched": matches[:8], "snapshots": snapshots[:20]}

    def _table_snapshot(self, page):
        best = None
        try:
            tables = page.locator("table")
            for i in range(min(tables.count(), 30)):
                table = tables.nth(i)
                if not table.is_visible():
                    continue
                headers = []
                try:
                    hs = table.locator("thead th")
                    for j in range(min(hs.count(), 20)):
                        headers.append(safe_text(hs.nth(j), 160))
                except Exception:
                    pass
                text = safe_text(table, 5200)
                blob = " ".join(headers).lower()
                semantic = ("serial" in blob and "trademark" in blob) or ("status" in blob and "registered" in blob) or "serial trademark status" in text.lower()
                if not semantic:
                    continue
                rows = []
                try:
                    trs = table.locator("tbody tr")
                    for j in range(min(trs.count(), 25)):
                        tr = trs.nth(j)
                        if not tr.is_visible():
                            continue
                        row_text = safe_text(tr, 1200)
                        if not row_text or "no data available" in row_text.lower():
                            continue
                        cells = []
                        tds = tr.locator("td")
                        for k in range(min(tds.count(), 12)):
                            cells.append(safe_text(tds.nth(k), 300))
                        rows.append({"text": row_text, "cells": cells})
                except Exception:
                    pass
                candidate = {"table_index": i, "headers": headers, "rows": rows[:5], "row_count_observed": len(rows), "table_text_excerpt": text[:1800]}
                if best is None or candidate["row_count_observed"] > best["row_count_observed"]:
                    best = candidate
        except Exception:
            pass
        return best or {"table_index": None, "headers": [], "rows": [], "row_count_observed": 0, "table_text_excerpt": ""}

    def _terminal_probe(self, page):
        body = ""
        try:
            body = norm(page.locator("body").inner_text(timeout=3000))
        except Exception:
            pass
        lower = body.lower()
        table = self._table_snapshot(page)
        totals = [int(x.replace(",", "")) for x in re.findall(r"Showing\s+\d+\s+to\s+\d+\s+of\s+([\d,]+)\s+results", body, re.I)]
        zero = bool(re.search(r"Showing\s+0\s+to\s+0\s+of\s+0\s+results", body, re.I)) or ("no data available in table" in lower and any(x == 0 for x in totals))
        control = any(x in lower for x in ("captcha", "verify you are human", "are you a robot", "human verification"))
        result = {"terminal": None, "table": table, "result_totals": totals[:20], "zero_marker": zero, "control_marker": control, "body_excerpt": body[:2200]}
        if control:
            result["terminal"] = "CONTROL_BLOCKED"
        elif table["row_count_observed"] > 0:
            result["terminal"] = "POSITIVE_ROWS"
        elif zero:
            result["terminal"] = "ZERO_RESULTSET"
        return result

    def query(self, mode, query, expected):
        page = self.browser.new_page(viewport={"width": 1440, "height": 1000})
        rec = {"resolver": "TMHUNT", "declared_scope": self.SCOPE, "mode": mode, "query": query, "expected": expected, "state": "CAPABILITY_UNPROVEN", "failure_signature": None}
        try:
            panel, panel_evidence = self._open_panel(page)
            rec["query_panel"] = panel_evidence
            rec["mode_control"] = self._select_mode(page, panel, mode)
            rec["active_mode_attestation"] = self._attest_mode(panel, mode)
            selected, candidates = choose_visible_search_input(panel)
            rec["input_candidates"] = candidates[:20]
            if not selected:
                rec["failure_signature"] = "TMHUNT_PANEL_SEARCH_INPUT_NOT_FOUND"
                return rec
            input_el, input_desc = selected
            rec["selected_input"] = input_desc
            if not rec["active_mode_attestation"]["attested"]:
                rec["failure_signature"] = "TMHUNT_ACTIVE_MODE_NOT_ATTESTED"
                return rec
            input_el.fill(query)
            rec["pre_submit_input_value"] = input_el.input_value(timeout=1500)
            rec["submission"] = submit_scoped(page, panel, input_el)
            terminal = wait_for(page, lambda: self._terminal_probe(page), timeout_seconds=15)
            rec["terminal_result"] = terminal
            rec["final_url"] = page.url
            rec["body_sha256"] = sha(page.content())
            rec["structured_rows"] = terminal.get("table", {}).get("rows", [])[:5]
            rec["row_count_observed"] = terminal.get("table", {}).get("row_count_observed", 0)
            rec["zero_marker"] = terminal.get("zero_marker", False)
            if terminal.get("terminal") == "CONTROL_BLOCKED":
                rec["state"] = "CAPABILITY_BLOCKED"
                rec["failure_signature"] = "TMHUNT_CONTROL_OR_HUMAN_VERIFICATION_OBSERVED"
            elif expected == "POSITIVE" and terminal.get("terminal") == "POSITIVE_ROWS" and rec["row_count_observed"] > 0:
                rec["state"] = "CAPABILITY_PASS"
            elif expected == "ZERO" and terminal.get("terminal") == "ZERO_RESULTSET":
                rec["state"] = "CAPABILITY_PASS"
            else:
                rec["failure_signature"] = "TMHUNT_DECLARED_CAPABILITY_SEMANTICS_NOT_BOUND"
        except Exception as exc:
            rec["state"] = "CAPABILITY_BLOCKED"
            rec["failure_signature"] = f"{type(exc).__name__}:{str(exc)[:220]}"
        finally:
            page.close()
        return rec
