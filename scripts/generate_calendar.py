
from __future__ import annotations
import hashlib
import os
from datetime import datetime, date, timedelta, timezone
from typing import List, Optional, Dict, Any

# ---- Configuration ----
CAL_TZ = 'Europe/London'  # For header metadata; events exported in UTC
OUTPUT_PATH = os.path.join('docs', 'calendar.ics')
CAL_NAME = 'Wembley Stadium Events'
CAL_DESC = 'Wembley Stadium events (updated daily).'
CAL_URL  = 'https://www.wembleystadium.com/events'

# ---- Minimal tzinfo for Europe/London is tricky w/out external libs.
# We'll accept input as naive/local London time and export as UTC.
# For accurate DST conversion, we rely on the OS tzdb via zoneinfo (Python 3.9+)
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
    LONDON = ZoneInfo('Europe/London')
except Exception:
    # Fallback: treat as UTC if zoneinfo is unavailable
    LONDON = timezone.utc

def fetch_events() -> List[Dict[str, Any]]:
    """
    Scrape Wembley Stadium events: https://www.wembleystadium.com/events
    Produces timed or all-day events depending on whether time is present (e.g., '17:00' or 'TBC').
    Titles are kept in English; output is UTF-8.
    """
    import re
    from urllib.request import urlopen, Request
    from urllib.parse import urljoin
    from bs4 import BeautifulSoup

    base = 'https://www.wembleystadium.com'
    url = urljoin(base, '/events')
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(req, timeout=30) as resp:
        html = resp.read()

    soup = BeautifulSoup(html, 'lxml')

    def parse_date_time(block_text: str):
        # Example date: '27 Sep 2025' ; time: '17:00' or 'TBC'
        m_date = re.search(r'(\d{2} \w{3} \d{4})', block_text)
        m_time = re.search(r'(\d{2}:\d{2}|TBC)', block_text, re.IGNORECASE)
        if not m_date:
            return None, None, False
        d = datetime.strptime(m_date.group(1), '%d %b %Y').date()
        if m_time and m_time.group(1).upper() != 'TBC':
            hh, mm = map(int, m_time.group(1).split(':'))
            start_dt = datetime(d.year, d.month, d.day, hh, mm)
            end_dt = start_dt + timedelta(hours=3)  # default duration
            return start_dt, end_dt, False
        else:
            # All-day when time is TBC
            return d, d + timedelta(days=1), True

    events: List[Dict[str, Any]] = []

    # Strategy: find all 'Find Out More' anchors, then read the surrounding block
    for a in soup.find_all('a'):
        if a.get_text(strip=True).lower().startswith('find out more'):
            card = a
            # climb up to a reasonable container
            for _ in range(8):
                card = card.parent
                if card is None:
                    break
                heading = card.find(['h2', 'h3'])
                if heading and heading.get_text(strip=True):
                    block_text = card.get_text('\n', strip=True)
                    start, end, all_day = parse_date_time(block_text)
                    if start is None:
                        continue
                    title = heading.get_text(strip=True)
                    # brief description: try the next text node near heading
                    description = ''
                    next_text = heading.find_next(string=True)
                    if next_text:
                        description = str(next_text).strip()
                    href = a.get('href') or ''
                    href = urljoin(base, href)

                    e: Dict[str, Any] = {
                        'title': title,
                        'location': 'Wembley Stadium, London',
                        'description': description,
                        'url': href,
                    }
                    if all_day:
                        e.update({'start': start, 'end': end, 'all_day': True})
                    else:
                        e.update({'start': start, 'end': end, 'all_day': False})

                    events.append(e)
                    break

    # de-duplicate by title + start
    dedup: Dict[str, Dict[str, Any]] = {}
    for e in events:
        key = f"{e['title']}|{e['start']}"
        dedup[key] = e

    out = sorted(dedup.values(), key=lambda x: (isinstance(x['start'], datetime), x['start']))

    return out


def _ensure_uid(e: Dict[str, Any]) -> str:
    base = f"{e.get('title','')}-{e.get('start')}-{e.get('end')}-{e.get('location','')}"
    h = hashlib.sha256(base.encode('utf-8')).hexdigest()[:16]
    return f"{h}@your-domain"


def _fmt_dt_utc(dt: datetime) -> str:
    # Ensure timezone-aware in London, then convert to UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=LONDON)
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc.strftime('%Y%m%dT%H%M%SZ')


def _fmt_date(d: date) -> str:
    return d.strftime('%Y%m%d')


def _sanitize(text: Optional[str]) -> str:
    if not text:
        return ''
    # Escape commas, semicolons, and newlines per RFC 5545
    return (
        text.replace('\\', '\\\\')
            .replace('\n', '\\n')
            .replace(',', '\\,')
            .replace(';', '\\;')
    )


def generate_ics(events: List[Dict[str, Any]]) -> str:
    now = datetime.now(timezone.utc)
    lines = [
        'BEGIN:VCALENDAR',
        'PRODID:-//YourOrg//ICS Feed//EN',
        'VERSION:2.0',
        f'X-WR-CALNAME:{_sanitize(CAL_NAME)}',
        f'X-WR-CALDESC:{_sanitize(CAL_DESC)}',
        f'X-WR-TIMEZONE:{CAL_TZ}',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
    ]

    for e in events:
        uid = e.get('uid') or _ensure_uid(e)
        title = _sanitize(e.get('title', 'Untitled'))
        desc = _sanitize(e.get('description', ''))
        loc  = _sanitize(e.get('location', ''))
        url  = _sanitize(e.get('url', ''))

        lines.append('BEGIN:VEVENT')
        lines.append(f'UID:{uid}')
        lines.append(f'DTSTAMP:{_fmt_dt_utc(now)}')

        all_day = bool(e.get('all_day', False))
        s = e.get('start')
        t = e.get('end')

        if all_day:
            # All-day events: DTSTART/DTEND in DATE form; DTEND is exclusive
            if isinstance(s, datetime):
                s = s.date()
            if isinstance(t, datetime):
                t = t.date()
            lines.append(f'DTSTART;VALUE=DATE:{_fmt_date(s)}')
            lines.append(f'DTEND;VALUE=DATE:{_fmt_date(t)}')
        else:
            # Timed events: export as UTC (Z)
            if isinstance(s, date) and not isinstance(s, datetime):
                s = datetime(s.year, s.month, s.day, 0, 0)
            if isinstance(t, date) and not isinstance(t, datetime):
                t = datetime(t.year, t.month, t.day, 0, 0)
            lines.append(f'DTSTART:{_fmt_dt_utc(s)}')
            lines.append(f'DTEND:{_fmt_dt_utc(t)}')

        lines.append(f'SUMMARY:{title}')
        if desc:
            lines.append(f'DESCRIPTION:{desc}')
        if loc:
            lines.append(f'LOCATION:{loc}')
        if url:
            lines.append(f'URL:{url}')
        lines.append('END:VEVENT')

    lines.append('END:VCALENDAR')
    return "\r\n".join(lines) + "\r\n"


def main():
    events = fetch_events()
    ics_text = generate_ics(events)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8', newline='') as f:
        f.write(ics_text)
    print(f"Wrote {OUTPUT_PATH} ({len(ics_text)} bytes)")


if __name__ == '__main__':
    main()
