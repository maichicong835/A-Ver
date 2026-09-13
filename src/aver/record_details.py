#!/usr/bin/env python3
import re


def _norm(value):
    return re.sub(r"\s+", " ", value or "").strip()


def parse_trademarkia_record_detail(body_text):
    """Normalize direct-record text into bounded evidence fields.

    This parser does not decide similarity, goods relatedness, or TM outcome.
    It only converts machine-observed direct record text into stable fields for
    the later G0-G4/materiality layer.
    """
    body = _norm(body_text)

    serial_match = re.search(r"\bSerial Number\s+#?(\d{8})\b", body, re.I)
    registration_match = re.search(r"\bRegistration(?: Number)?\s+#?(\d{5,9})\b", body, re.I)
    registered_on_match = re.search(r"\bRegistered On\s+([^|]{6,40}?)(?=\s+(?:First Use Date|Serial Number|Previous slide|SUMMARY|$))", body, re.I)
    category_match = re.search(r"\bfiled in the category of\s+(.+?)(?:\.| The company| As of|$)", body, re.I)
    disclaimer_match = re.search(r"\bDisclaimer\s+(.+?)(?=\s+FILING SECTIONS\b|$)", body, re.I)

    class_blocks = []
    pattern = re.compile(
        r"\bProduct Class\s+Class\s+0*(\d{1,3})\s+(.*?)(?=(?:\bProduct Class\s+Class\s+0*\d{1,3}\b|\bOWNER CONTACT INFORMATION\b|\bCORRESPONDENT CONTACT INFORMATION\b|\bTM TRADEMARK DETAILS\b|$))",
        re.I,
    )
    for match in pattern.finditer(body):
        class_code = str(int(match.group(1))).zfill(3)
        raw_block = _norm(match.group(2))
        goods_text = raw_block
        # Remove category label and first-use metadata while preserving the
        # observed goods/services text that follows it.
        commerce = re.search(r"\bFirst Use Date \(Commerce\)\s+\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s+", raw_block, re.I)
        if commerce:
            goods_text = _norm(raw_block[commerce.end():])
        else:
            general = re.search(r"\bFirst Use Date \(General\)\s+\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s+", raw_block, re.I)
            if general:
                goods_text = _norm(raw_block[general.end():])
        goods_text = re.sub(r"\s+Read more\s*$", "", goods_text, flags=re.I).strip()
        class_blocks.append({
            "class_code": class_code,
            "raw_class_block": raw_block[:4000],
            "goods_services_text": goods_text[:3000],
            "goods_services_text_nonempty": bool(goods_text),
        })

    return {
        "serial_number": serial_match.group(1) if serial_match else None,
        "registration_number": registration_match.group(1) if registration_match else None,
        "registered_on": _norm(registered_on_match.group(1)) if registered_on_match else None,
        "category": _norm(category_match.group(1)) if category_match else None,
        "disclaimer_text": _norm(disclaimer_match.group(1)) if disclaimer_match else None,
        "class_details": class_blocks,
        "class_codes": [x["class_code"] for x in class_blocks],
        "structured_detail_complete": bool(serial_match and registration_match and class_blocks and all(x["goods_services_text_nonempty"] for x in class_blocks)),
    }
