#!/usr/bin/env python3
from __future__ import annotations
import csv
import datetime as dt
import json
import os
from collections import defaultdict
from typing import Dict, List, Optional, Set

from src.keywords.expand import build_series_keywords
from src.matching.score import compute_score
from src.platforms.dailymotion import search_videos


def load_data(path: str) -> Dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _int_env(name: str, default: int, minimum: int = 1) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
        return value if value >= minimum else minimum
    except ValueError:
        return default


def _float_env(name: str, default: float, minimum: float = 0.0) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
        return value if value >= minimum else default
    except ValueError:
        return default


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y"}


def build_aliases_map(data: Dict) -> Dict[str, List[str]]:
    m: Dict[str, List[str]] = defaultdict(list)
    for a in data.get('aliases', []):
        sid = a.get('series_id')
        name = a.get('name')
        if not sid or not name:
            continue
        m[sid].append(name)
    return m


def build_title_map(data: Dict) -> Dict[str, str]:
    titles: Dict[str, str] = {}
    for item in data.get('series', []):
        sid = item.get('series_id')
        title = item.get('canonical_title') or ''
        if sid:
            titles[sid] = title
    return titles


def is_whitelisted(uploader_name: str, data: Dict) -> bool:
    for w in data.get('whitelist', []):
        if w.get('platform') == 'dailymotion':
            # If we later add DM whitelist; for now none -> False
            pass
        if w.get('platform') == 'youtube':
            # Not applicable to DM
            continue
    return False


def main():
    data_path = os.environ.get('DATA_JSON', 'data/data.json')
    out_dir = os.environ.get('REPORT_DIR', 'reports')
    os.makedirs(out_dir, exist_ok=True)
    state_dir = os.environ.get('STATE_DIR', 'state')
    os.makedirs(state_dir, exist_ok=True)
    state_path = os.path.join(state_dir, 'dailymotion_videos.json')

    data = load_data(data_path)
    aliases_by_sid = build_aliases_map(data)
    titles_by_sid = build_title_map(data)
    max_aliases = _int_env('DAILYMOTION_MAX_ALIASES', 10)
    include_ep_patterns = _bool_env('DAILYMOTION_INCLUDE_EP_PATTERNS', False)
    keywords_by_sid = build_series_keywords(
        data,
        include_ep_patterns=include_ep_patterns,
        max_aliases=max_aliases,
    )

    raw_filter = os.environ.get('DAILYMOTION_SERIES_IDS')
    series_filter: Optional[Set[str]] = None
    if raw_filter:
        series_filter = {s.strip() for s in raw_filter.split(',') if s.strip()}
        if series_filter:
            keywords_by_sid = {
                sid: terms for sid, terms in keywords_by_sid.items() if sid in series_filter
            }
            aliases_by_sid = {
                sid: aliases for sid, aliases in aliases_by_sid.items() if sid in keywords_by_sid
            }
            titles_by_sid = {
                sid: title for sid, title in titles_by_sid.items() if sid in keywords_by_sid
            }

    per_term_limit = _int_env('DAILYMOTION_PER_TERM_LIMIT', 12)
    sleep_sec = _float_env('DAILYMOTION_SLEEP_SEC', 0.3)

    # Query Dailymotion
    all_hits: List[Dict] = []
    total_series = len(keywords_by_sid)
    if total_series == 0:
        if series_filter:
            print('No series matched requested DAILYMOTION_SERIES_IDS; exiting.')
        else:
            print('No series available for querying; exiting.')
        return
    print(f'Searching Dailymotion for {total_series} series (limit {per_term_limit} per term, sleep {sleep_sec:.2f}s)')
    for idx, (sid, terms) in enumerate(keywords_by_sid.items(), start=1):
        aliases = aliases_by_sid.get(sid, [])
        title_hint = titles_by_sid.get(sid) or (aliases[0] if aliases else sid)
        print(f'[{idx}/{total_series}] {title_hint} -> {len(terms)} terms')
        hits = search_videos(terms, per_term_limit=per_term_limit, sleep_sec=sleep_sec)
        if hits:
            print(f'  Retrieved {len(hits)} candidates')
        for h in hits:
            h['__series_id'] = sid
        all_hits.extend(hits)
    print(f'Collected {len(all_hits)} raw candidates before dedupe')

    # Deduplicate by (platform, video_id)
    dedup: Dict[str, Dict] = {}
    for h in all_hits:
        vid = h.get('id')
        if not vid:
            continue
        key = f'dailymotion:{vid}'
        if key in dedup:
            continue
        dedup[key] = h
    print(f'{len(dedup)} unique candidates after dedupe')

    # Load previous state
    prev_state: Dict[str, Dict] = {}
    if os.path.exists(state_path):
        with open(state_path, 'r', encoding='utf-8') as f:
            prev_state = json.load(f)

    today = dt.date.today()
    today_s = today.isoformat()

    # Score and compute status
    new_state: Dict[str, Dict] = {}
    rows: List[List[str]] = []
    for key, h in dedup.items():
        title = h.get('title', '')
        sid = h.get('__series_id')
        aliases = aliases_by_sid.get(sid, [])
        score = compute_score(title, aliases)
        uploader = h.get('owner.username') or ''
        whitelisted = is_whitelisted(uploader, data)
        if whitelisted:
            score -= 2.0

        prev = prev_state.get(key)
        first_seen = prev.get('first_seen') if prev else today_s
        last_seen = today_s
        status = 'new' if not prev else 'active'
        # Determine likely_removed for entries not re-seen will be handled next run

        new_state[key] = {
            'platform': 'dailymotion',
            'video_id': h.get('id'),
            'url': h.get('url'),
            'title': title,
            'uploader': uploader,
            'duration_sec': h.get('duration'),
            'publish_time': h.get('created_time'),
            'views': h.get('views_total'),
            'score': round(score, 3),
            'series_id': sid,
            'first_seen': first_seen,
            'last_seen': last_seen,
            'source_term': h.get('__source_term'),
            'status': status,
        }
        rows.append([
            'dailymotion', h.get('id', ''), title, h.get('url', ''), uploader,
            str(h.get('created_time', '')), str(h.get('duration', '')), str(h.get('views_total', '')),
            f"{score:.3f}", status
        ])

    # Write state
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(new_state, f, ensure_ascii=False, indent=2)

    # Write report CSV
    out_csv = os.path.join(out_dir, f'dailymotion_candidates_{today_s}.csv')
    with open(out_csv, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['platform', 'video_id', 'title', 'url', 'uploader', 'publish_time', 'duration_sec', 'views', 'score', 'status'])
        # Sort: score desc, publish_time desc (string), views desc
        def sort_key(r):
            try:
                views = int(r[7]) if r[7].isdigit() else 0
            except Exception:
                views = 0
            return (-float(r[8]), r[5], -views)
        for r in sorted(rows, key=sort_key):
            w.writerow(r)

    print(f'Wrote {out_csv} with {len(rows)} rows')


if __name__ == '__main__':
    main()
