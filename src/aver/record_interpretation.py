#!/usr/bin/env python3
import re


def normalize_text(value):
    return re.sub(r"\s+", " ", value or "").strip()


def bind_record_anchor(body_text, mark_text, serial, expected_class=None, before=500, after=1400, max_mark_serial_gap=80):
    body = normalize_text(body_text)
    mark = normalize_text(mark_text)
    serial = str(serial).strip()
    pos = body.find(serial)
    if pos < 0:
        return {"bound": False, "failure_signature": "SERIAL_NOT_FOUND"}

    left_start = max(0, pos - before)
    left = body[left_start:pos]
    mark_pos = left.lower().rfind(mark.lower()) if mark else -1
    if mark_pos < 0:
        return {"bound": False, "failure_signature": "MARK_NOT_BOUND_TO_SERIAL"}

    between = left[mark_pos + len(mark):]
    low_between = between.lower()
    if "mark details" in low_between or "class/description" in low_between:
        return {"bound": False, "failure_signature": "MARK_CROSSES_RESULT_HEADER", "identifier": serial, "mark_text": mark}
    if len(between) > max_mark_serial_gap:
        return {"bound": False, "failure_signature": "MARK_TOO_FAR_FROM_SERIAL", "identifier": serial, "mark_text": mark, "gap": len(between)}

    after_serial = body[pos + len(serial):pos + len(serial) + after]
    next_serial = re.search(r"\b\d{8}\b", after_serial)
    record_tail = after_serial[:next_serial.start()] if next_serial else after_serial

    status_match = re.search(
        r"\b(Live/(?:Registered|Pending)|Dead/(?:Cancelled|Abandoned)|Registered|Pending)\b(?:\s+on\s+\d{1,2}\s+[A-Za-z]{3}\s+\d{4})?",
        record_tail,
        re.I,
    )
    class_matches = list(re.finditer(r"\bClass\s+(\d{3})\b", record_tail, re.I))
    classes = []
    for match in class_matches:
        value = match.group(1)
        if value not in classes:
            classes.append(value)

    if not status_match:
        return {"bound": False, "failure_signature": "STATUS_NOT_BOUND", "identifier": serial, "mark_text": mark}
    if not classes:
        return {"bound": False, "failure_signature": "CLASS_CONTEXT_NOT_BOUND", "identifier": serial, "mark_text": mark}
    if expected_class and expected_class not in classes:
        return {"bound": False, "failure_signature": "EXPECTED_CLASS_NOT_BOUND", "identifier": serial, "mark_text": mark, "classes": classes}

    mark_abs = left_start + mark_pos
    record_end = pos + len(serial) + class_matches[-1].end()
    context = body[mark_abs:record_end]
    return {
        "bound": True,
        "mark_text": mark,
        "identifier": serial,
        "status": status_match.group(0),
        "classes": classes,
        "expected_class": expected_class,
        "mark_to_serial_gap": len(between),
        "next_serial_boundary_observed": next_serial is not None,
        "class_or_goods_services_context": context,
    }


def discover_record_anchors_from_page(page, limit=12):
    """Observe actual Trademarkia record anchors after a resultset is terminal.

    This function is deliberately separate from transport polling. It only reads
    the already-rendered page, rejects navigation links, and returns bounded raw
    anchor/container evidence. It does not make TM decisions.
    """
    found = []
    seen = set()
    anchors = page.locator("a[href]")
    for i in range(min(anchors.count(), 500)):
        if len(found) >= limit:
            break
        el = anchors.nth(i)
        try:
            if not el.is_visible():
                continue
            href = el.get_attribute("href") or ""
        except Exception:
            continue
        m = re.search(r"-(\d{8})(?:[/?#]|$)", href)
        if not m:
            continue
        serial = m.group(1)
        if serial in seen:
            continue
        try:
            snapshot = el.evaluate(
                """el => {
                  let n = el;
                  let best = null;
                  for (let depth = 0; depth < 8 && n; depth++, n = n.parentElement) {
                    const t = (n.innerText || '').replace(/\s+/g, ' ').trim();
                    const hasSerial = /\b\d{8}\b/.test(t);
                    const hasStatus = /(Live\/(Registered|Pending)|Dead\/(Cancelled|Abandoned)|Registered|Pending)/i.test(t);
                    const hasClass = /Class\s+\d{3}/i.test(t);
                    if (t.length >= 30 && t.length <= 2400 && hasSerial && hasStatus && hasClass) {
                      best = n;
                      break;
                    }
                  }
                  const root = best || el.parentElement || el;
                  return {
                    href: el.href || el.getAttribute('href') || '',
                    anchorText: (el.innerText || '').replace(/\s+/g, ' ').trim(),
                    containerText: (root.innerText || '').replace(/\s+/g, ' ').trim()
                  };
                }"""
            )
        except Exception:
            continue
        container = normalize_text(snapshot.get("containerText") or "")
        if serial not in container:
            continue
        found.append({
            "identifier": serial,
            "record_url": snapshot.get("href") or href,
            "anchor_text": normalize_text(snapshot.get("anchorText") or ""),
            "container_text": container[:2000],
        })
        seen.add(serial)
    return found
