#!/usr/bin/env python3
import hashlib
import json
import re
import time


def sha(value):
    if isinstance(value, str):
        value = value.encode("utf-8", errors="replace")
    return hashlib.sha256(value).hexdigest()


def norm(value):
    return re.sub(r"\s+", " ", value or "").strip()


def safe_text(locator, limit=1600):
    try:
        return norm(locator.inner_text(timeout=3000))[:limit]
    except Exception:
        return ""


def attrs(locator):
    try:
        return locator.evaluate(
            """el => ({
              tag: el.tagName,
              id: el.id || null,
              name: el.getAttribute('name'),
              value: el.getAttribute('value'),
              type: el.getAttribute('type'),
              role: el.getAttribute('role'),
              ariaSelected: el.getAttribute('aria-selected'),
              ariaPressed: el.getAttribute('aria-pressed'),
              ariaChecked: el.getAttribute('aria-checked'),
              placeholder: el.getAttribute('placeholder'),
              className: el.className || null
            })"""
        )
    except Exception:
        return {}


def choose_visible_search_input(root):
    candidates = []
    for selector in ["textarea", "input[type='search']", "input[type='text']", "input:not([type])"]:
        try:
            loc = root.locator(selector)
            for i in range(min(loc.count(), 30)):
                el = loc.nth(i)
                if not el.is_visible():
                    continue
                desc = attrs(el)
                try:
                    desc["value_now"] = el.input_value(timeout=1200)
                except Exception:
                    pass
                candidates.append((el, desc))
        except Exception:
            continue

    def score(item):
        _el, desc = item
        s = 0
        if desc.get("tag") == "TEXTAREA":
            s += 5
        if desc.get("type") == "search":
            s += 5
        blob = " ".join(str(desc.get(k) or "") for k in ("id", "name", "placeholder")).lower()
        if any(k in blob for k in ("search", "query", "mark", "trademark")):
            s += 3
        return s

    candidates.sort(key=score, reverse=True)
    return (candidates[0] if candidates else None), [d for _, d in candidates]


def submit_scoped(page, root, input_el):
    evidence = {"method": None, "control": None}
    roots = []
    try:
        form = input_el.locator("xpath=ancestor::form[1]")
        if form.count():
            roots.append(("form", form.first))
    except Exception:
        pass
    roots.append(("scope", root))

    for root_name, candidate_root in roots:
        for selector in ["button:has-text('Search')", "button[type='submit']", "input[type='submit']"]:
            try:
                loc = candidate_root.locator(selector)
                for i in range(min(loc.count(), 15)):
                    el = loc.nth(i)
                    if not el.is_visible():
                        continue
                    evidence["method"] = f"{root_name}:{selector}"
                    evidence["control"] = {"text": safe_text(el, 260), "attrs": attrs(el)}
                    el.click()
                    return evidence
            except Exception:
                continue
    input_el.press("Enter")
    evidence["method"] = "input:Enter"
    return evidence


def wait_for(page, probe, timeout_seconds=15, interval_ms=450):
    deadline = time.time() + timeout_seconds
    last = None
    while time.time() < deadline:
        last = probe()
        if last.get("terminal"):
            return last
        page.wait_for_timeout(interval_ms)
    last = last or {}
    last["terminal"] = "TIMEOUT"
    return last


def compact_json(value):
    return norm(json.dumps(value, sort_keys=True))
