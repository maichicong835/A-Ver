#!/usr/bin/env python3
import re


def normalize_text(value):
    return re.sub(r"\s+", " ", value or "").strip()


def bind_record_anchor(body_text, mark_text, serial, expected_class=None, before=500, after=1400):
    """Bind a known mark+serial anchor to nearby status/class/goods context.

    This is an interpretation primitive, not a search resolver. It consumes
    already-captured resultset text and never upgrades a resultset to TM PASS.
    """
    body = normalize_text(body_text)
    mark = normalize_text(mark_text)
    serial = str(serial).strip()
    pos = body.find(serial)
    if pos < 0:
        return {"bound": False, "failure_signature": "SERIAL_NOT_FOUND"}

    left = body[max(0, pos - before):pos]
    mark_pos = left.lower().rfind(mark.lower()) if mark else -1
    if mark_pos < 0:
        return {"bound": False, "failure_signature": "MARK_NOT_BOUND_TO_SERIAL"}

    tail = body[pos:pos + after]
    status_match = re.search(
        r"\b(Live/(?:Registered|Pending)|Dead/(?:Cancelled|Abandoned)|Registered|Pending)\b(?:\s+on\s+\d{1,2}\s+[A-Za-z]{3}\s+\d{4})?",
        tail,
        re.I,
    )
    classes = []
    for value in re.findall(r"\bClass\s+(\d{3})\b", tail, re.I):
        if value not in classes:
            classes.append(value)

    if not status_match:
        return {"bound": False, "failure_signature": "STATUS_NOT_BOUND", "identifier": serial, "mark_text": mark}
    if not classes:
        return {"bound": False, "failure_signature": "CLASS_CONTEXT_NOT_BOUND", "identifier": serial, "mark_text": mark}
    if expected_class and expected_class not in classes:
        return {
            "bound": False,
            "failure_signature": "EXPECTED_CLASS_NOT_BOUND",
            "identifier": serial,
            "mark_text": mark,
            "classes": classes,
        }

    context_start = max(0, pos - min(240, before))
    context = body[context_start:pos + after]
    return {
        "bound": True,
        "mark_text": mark,
        "identifier": serial,
        "status": status_match.group(0),
        "classes": classes,
        "expected_class": expected_class,
        "class_or_goods_services_context": context,
    }
