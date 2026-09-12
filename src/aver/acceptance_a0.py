#!/usr/bin/env python3
import hashlib
import json
import os
import platform
import socket
import ssl
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

ENGINE_VERSION = "0.1.0"
PHASE = "A0_TRANSPORT"
OUT_DIR = Path("artifacts/a0")
OUT_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = [
    {
        "resolver": "TMHUNT",
        "surface": "HOME",
        "url": "http://www.tmhunt.com/",
        "required_markers": ["tmhunt", "trademark"]
    },
    {
        "resolver": "TMHUNT",
        "surface": "HELP",
        "url": "http://www.tmhunt.com/help.php",
        "required_markers": ["tmhunt", "trademark", "exact"]
    },
    {
        "resolver": "TRADEMARKIA",
        "surface": "SEARCH",
        "url": "https://www.trademarkia.com/trademark/search",
        "required_markers": ["trademarkia", "trademark"]
    }
]

class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == "form":
            self.current = {
                "method": (attrs.get("method") or "GET").upper(),
                "action": attrs.get("action") or "",
                "inputs": [],
                "selects": []
            }
            self.forms.append(self.current)
        elif self.current is not None and tag.lower() == "input":
            self.current["inputs"].append({
                "name": attrs.get("name"),
                "type": attrs.get("type", "text"),
                "value": attrs.get("value")
            })
        elif self.current is not None and tag.lower() == "select":
            self.current["selects"].append({"name": attrs.get("name")})

    def handle_endtag(self, tag):
        if tag.lower() == "form":
            self.current = None


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def fetch_target(target):
    started = now_iso()
    t0 = time.monotonic()
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 A-Ver-Acceptance/0.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.8",
        "Cache-Control": "no-cache"
    }
    request = Request(target["url"], headers=headers, method="GET")
    opener = build_opener(HTTPRedirectHandler())
    record = {
        "resolver": target["resolver"],
        "surface": target["surface"],
        "requested_url": target["url"],
        "started_at_utc": started,
        "transport_state": "TRANSPORT_BLOCKED",
        "surface_identity_state": "SURFACE_IDENTITY_UNRESOLVED",
        "failure_signature": None,
        "http_status": None,
        "final_url": None,
        "content_type": None,
        "response_bytes": 0,
        "response_sha256": None,
        "required_markers": target["required_markers"],
        "matched_markers": [],
        "forms": []
    }
    body = b""
    try:
        with opener.open(request, timeout=20) as response:
            body = response.read(2_000_000)
            record["http_status"] = getattr(response, "status", None) or response.getcode()
            record["final_url"] = response.geturl()
            record["content_type"] = response.headers.get("Content-Type")
            record["transport_state"] = "TRANSPORT_PASS" if 200 <= record["http_status"] < 400 else "TRANSPORT_HTTP_ERROR"
    except HTTPError as exc:
        record["http_status"] = exc.code
        record["final_url"] = exc.geturl()
        record["content_type"] = exc.headers.get("Content-Type") if exc.headers else None
        try:
            body = exc.read(256_000)
        except Exception:
            body = b""
        record["failure_signature"] = f"HTTP_{exc.code}"
        record["transport_state"] = "TRANSPORT_HTTP_ERROR"
    except (URLError, socket.timeout, ssl.SSLError, TimeoutError) as exc:
        reason = getattr(exc, "reason", exc)
        record["failure_signature"] = f"NETWORK_{type(reason).__name__}:{str(reason)[:180]}"
        record["transport_state"] = "TRANSPORT_NETWORK_ERROR"
    except Exception as exc:
        record["failure_signature"] = f"UNEXPECTED_{type(exc).__name__}:{str(exc)[:180]}"
        record["transport_state"] = "TRANSPORT_UNEXPECTED_ERROR"

    record["response_bytes"] = len(body)
    record["response_sha256"] = sha256_bytes(body) if body else None
    text = body.decode("utf-8", errors="ignore")
    lower = text.lower()
    record["matched_markers"] = [m for m in target["required_markers"] if m.lower() in lower]

    if record["transport_state"] == "TRANSPORT_PASS":
        if record["matched_markers"]:
            record["surface_identity_state"] = "SURFACE_IDENTITY_PASS"
        else:
            record["surface_identity_state"] = "SURFACE_IDENTITY_UNRESOLVED"
            record["failure_signature"] = record["failure_signature"] or "EXPECTED_MARKERS_NOT_OBSERVED"

        parser = FormParser()
        try:
            parser.feed(text[:1_500_000])
            record["forms"] = parser.forms[:20]
        except Exception as exc:
            record["forms_parse_warning"] = f"{type(exc).__name__}:{str(exc)[:160]}"

    record["finished_at_utc"] = now_iso()
    record["elapsed_ms"] = round((time.monotonic() - t0) * 1000)
    return record


def resolver_state(records, resolver):
    rs = [r for r in records if r["resolver"] == resolver]
    if not rs:
        return "NOT_TESTED"
    if all(r["transport_state"] == "TRANSPORT_PASS" and r["surface_identity_state"] == "SURFACE_IDENTITY_PASS" for r in rs):
        return "A0_TRANSPORT_PASS"
    if any(r["transport_state"] == "TRANSPORT_PASS" and r["surface_identity_state"] == "SURFACE_IDENTITY_PASS" for r in rs):
        return "A0_TRANSPORT_PARTIAL"
    return "A0_TRANSPORT_BLOCKED"


def main():
    start = now_iso()
    records = [fetch_target(t) for t in TARGETS]
    states = {
        "TMHUNT": resolver_state(records, "TMHUNT"),
        "TRADEMARKIA": resolver_state(records, "TRADEMARKIA")
    }
    if all(v == "A0_TRANSPORT_PASS" for v in states.values()):
        phase_state = "A0_PASS"
    elif any(v in ("A0_TRANSPORT_PASS", "A0_TRANSPORT_PARTIAL") for v in states.values()):
        phase_state = "A0_PARTIAL"
    else:
        phase_state = "A0_BLOCKED"

    receipt = {
        "schema": "AVER_ACCEPTANCE_RECEIPT",
        "engine_version": ENGINE_VERSION,
        "mode": "ACCEPTANCE_ONLY",
        "phase": PHASE,
        "authority": {
            "repository": os.getenv("GITHUB_REPOSITORY", "UNKNOWN"),
            "commit_sha": os.getenv("GITHUB_SHA", "UNKNOWN"),
            "workflow_run_id": os.getenv("GITHUB_RUN_ID", "UNKNOWN"),
            "workflow_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT", "UNKNOWN")
        },
        "runner": {
            "os": platform.platform(),
            "python": sys.version.split()[0]
        },
        "started_at_utc": start,
        "finished_at_utc": now_iso(),
        "phase_state": phase_state,
        "resolver_states": states,
        "production_tm_decision_authorized": False,
        "external_side_effects_authorized": False,
        "candidate_queries_executed": False,
        "negative_clearance_inferred": False,
        "records": records,
        "next_action": {
            "A0_PASS": "PROCEED_TO_A1_KNOWN_POSITIVE_BINDING_WITH_FIXED_CANARIES",
            "A0_PARTIAL": "REPAIR_ONLY_FAILED_RESOLVER_TRANSPORT_OR_SURFACE_IDENTITY;_DO_NOT_QUERY_CANDIDATES",
            "A0_BLOCKED": "STOP_ACCEPTANCE_AT_TRANSPORT;CHANGE_TRANSPORT_DIMENSION_OR_HOLD_CAPABILITY"
        }[phase_state]
    }

    output = OUT_DIR / "a0-receipt.json"
    output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "phase_state": phase_state,
        "resolver_states": states,
        "receipt": str(output)
    }, indent=2))

    # A0_PARTIAL/BLOCKED are evidence outcomes, not workflow infrastructure failures.
    # Exit nonzero only if the acceptance harness itself violates its contract.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
