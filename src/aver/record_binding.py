#!/usr/bin/env python3
import hashlib
import html
import re
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 A-Ver/0.1'


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        if data and data.strip():
            self.parts.append(data.strip())

    def text(self):
        return re.sub(r'\s+', ' ', html.unescape(' '.join(self.parts))).strip()


def slugify(mark_text):
    return re.sub(r'[^a-z0-9]+', '-', (mark_text or '').lower()).strip('-')


def fetch_public_record(url, limit=2_000_000):
    rec = {'requested_url': url, 'status': None, 'final_url': None, 'bytes': 0, 'sha256': None, 'error': None}
    body = b''
    req = Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8', 'Accept-Language': 'en-US,en;q=0.8'})
    try:
        with build_opener(HTTPRedirectHandler()).open(req, timeout=25) as r:
            body = r.read(limit)
            rec['status'] = getattr(r, 'status', None) or r.getcode()
            rec['final_url'] = r.geturl()
    except HTTPError as exc:
        rec['status'] = exc.code
        rec['final_url'] = exc.geturl()
        rec['error'] = f'HTTP_{exc.code}'
        try:
            body = exc.read(256000)
        except Exception:
            pass
    except URLError as exc:
        rec['error'] = f'NETWORK_{type(getattr(exc, "reason", exc)).__name__}:{str(getattr(exc, "reason", exc))[:160]}'
    except Exception as exc:
        rec['error'] = f'{type(exc).__name__}:{str(exc)[:160]}'
    rec['bytes'] = len(body)
    rec['sha256'] = hashlib.sha256(body).hexdigest() if body else None
    return rec, body.decode('utf-8', errors='ignore')


def labeled_context(text, labels, max_chars=2200):
    lower = text.lower()
    starts = []
    for label in labels:
        pos = lower.find(label.lower())
        if pos >= 0:
            starts.append((pos, label))
    if not starts:
        return {'label': None, 'excerpt': None}
    pos, label = min(starts, key=lambda x: x[0])
    excerpt = text[pos:pos + max_chars]
    return {'label': label, 'excerpt': excerpt}


def bind_trademarkia_record(mark_text, serial):
    slug = slugify(mark_text)
    url = f'https://www.trademarkia.com/{quote(slug)}-{serial}'
    fetch, source = fetch_public_record(url)
    parser = TextParser()
    try:
        parser.feed(source[:1_800_000])
    except Exception:
        pass
    text = parser.text()
    lower = text.lower()
    expected_words = [x for x in re.findall(r'[a-z0-9]+', mark_text.lower()) if len(x) > 1]
    mark_seen = bool(expected_words) and all(x in lower for x in expected_words)
    serial_seen = serial in text
    status_tokens = [x for x in ('live', 'registered', 'pending', 'dead', 'cancelled', 'abandoned') if x in lower]
    class_codes = sorted(set(re.findall(r'(?:class|international class)\s*0?(\d{1,3})\b', lower)))
    class_codes = [x.zfill(3) for x in class_codes]
    registration_numbers = sorted(set(re.findall(r'(?:registration(?: number| no\.?| #)?)[^0-9]{0,20}(\d{6,8})', lower)))[:8]

    goods_context = labeled_context(text, ['Goods and Services', 'Goods & Services', 'Goods/Services'])
    goods_excerpt = goods_context['excerpt'] or ''
    goods_lower = goods_excerpt.lower()
    scoped_goods_markers = []
    for token in ('stickers','sticker','stationery','notebooks','handbags','printed','paper goods','clothing','apparel'):
        if token in goods_lower:
            scoped_goods_markers.append(token)

    disclaimer_context = labeled_context(text, ['Disclaimer', 'Disclaimed'])
    state = 'RECORD_BINDING_PASS' if fetch['status'] == 200 and serial_seen and mark_seen and status_tokens and class_codes else 'RECORD_BINDING_INCOMPLETE'
    return {
        'resolver': 'TRADEMARKIA_PUBLIC_RECORD',
        'serial': serial,
        'expected_mark': mark_text,
        'record_url': url,
        'fetch': fetch,
        'state': state,
        'serial_seen': serial_seen,
        'mark_seen': mark_seen,
        'status_tokens': status_tokens[:8],
        'class_codes': class_codes[:12],
        'registration_numbers': registration_numbers,
        'goods_services_label': goods_context['label'],
        'goods_services_excerpt': goods_excerpt[:2200] if goods_excerpt else None,
        'scoped_goods_markers': scoped_goods_markers,
        'whole_page_goods_markers_not_authoritative': True,
        'disclaimer_excerpt': disclaimer_context['excerpt'][:500] if disclaimer_context['excerpt'] else None,
        'body_sha256': fetch.get('sha256'),
        'legal_clearance_asserted': False,
    }
