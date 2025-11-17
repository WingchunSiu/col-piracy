#!/usr/bin/env python3
"""Dailymotion detection pipeline using Supabase database."""
from __future__ import annotations
import csv
import datetime as dt
import json
import os
import time
from typing import Dict, List, Optional, Set

from src.keywords.expand import build_series_keywords
from src.matching.score import compute_score
from src.platforms.dailymotion import search_videos
from src.database.supabase_db import get_existing_video_ids, insert_videos, count_videos


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


def _normalize_score(raw: float, scale: float) -> float:
    score = raw * scale
    return max(0.0, min(10.0, score))


def build_title_map(data: Dict) -> Dict[str, str]:
    titles = {}
    for item in data.get('series', []):
        sid = item.get('series_id')
        title = item.get('canonical_title') or ''
        if sid:
            titles[sid] = title
    return titles


def main():
    data_path = os.environ.get('DATA_JSON', 'data/data.json')
    out_dir = os.environ.get('REPORT_DIR', 'reports')
    os.makedirs(out_dir, exist_ok=True)

    data = load_data(data_path)
    max_aliases = _int_env('DAILYMOTION_MAX_ALIASES', 10)
    include_ep_patterns = _bool_env('DAILYMOTION_INCLUDE_EP_PATTERNS', False)
    min_alias_length = _int_env('DAILYMOTION_MIN_ALIAS_LENGTH', 6, minimum=0)

    keywords_by_sid_raw, filtered_aliases_by_sid = build_series_keywords(
        data,
        include_ep_patterns=include_ep_patterns,
        max_aliases=max_aliases,
        min_alias_length=min_alias_length,
    )

    aliases_by_sid = filtered_aliases_by_sid
    titles_by_sid = build_title_map(data)
    keywords_by_sid = keywords_by_sid_raw

    # Optional series filter
    raw_filter = os.environ.get('DAILYMOTION_SERIES_IDS')
    if raw_filter:
        series_filter = {s.strip() for s in raw_filter.split(',') if s.strip()}
        if series_filter:
            keywords_by_sid = {sid: terms for sid, terms in keywords_by_sid.items() if sid in series_filter}
            aliases_by_sid = {sid: aliases for sid, aliases in aliases_by_sid.items() if sid in keywords_by_sid}
            titles_by_sid = {sid: title for sid, title in titles_by_sid.items() if sid in keywords_by_sid}

    # Config
    per_term_limit = _int_env('DAILYMOTION_PER_TERM_LIMIT', 300)
    primary_aliases = _int_env('DAILYMOTION_PRIMARY_ALIASES', 2, minimum=0)
    primary_per_term_limit = _int_env('DAILYMOTION_PRIMARY_PER_TERM_LIMIT', max(per_term_limit, 1), minimum=1)
    sleep_sec = _float_env('DAILYMOTION_SLEEP_SEC', 0.2)
    score_scale = _float_env('DAILYMOTION_SCORE_SCALE', 6.0, minimum=0.1)
    min_duration_sec = _int_env('DAILYMOTION_MIN_DURATION_SEC', 1000, minimum=0)
    min_score = _float_env('DAILYMOTION_MIN_SCORE', 5.5, minimum=0.0)

    # Search Dailymotion
    total_series = len(keywords_by_sid)
    if total_series == 0:
        print('No series available; exiting.')
        return

    print(f'Searching Dailymotion for {total_series} series (limit {per_term_limit}/term, sleep {sleep_sec:.2f}s)')

    all_hits: List[Dict] = []
    for idx, (sid, terms) in enumerate(keywords_by_sid.items(), start=1):
        aliases = aliases_by_sid.get(sid, [])
        title_hint = titles_by_sid.get(sid) or (aliases[0] if aliases else sid)
        print(f'[{idx}/{total_series}] {title_hint} -> {len(terms)} terms')

        series_hits = []
        # Primary terms get higher limit
        primary_terms = terms[:primary_aliases] if primary_aliases > 0 else []
        secondary_terms = terms[primary_aliases:] if primary_aliases > 0 else terms

        if primary_terms:
            series_hits.extend(search_videos(primary_terms, per_term_limit=primary_per_term_limit, sleep_sec=sleep_sec))
        if secondary_terms:
            series_hits.extend(search_videos(secondary_terms, per_term_limit=per_term_limit, sleep_sec=sleep_sec))

        if series_hits:
            print(f'  Retrieved {len(series_hits)} candidates')

        for h in series_hits:
            h['__series_id'] = sid

        all_hits.extend(series_hits)

    print(f'Collected {len(all_hits)} raw candidates')

    # Deduplicate by video_id
    dedup: Dict[str, Dict] = {}
    for h in all_hits:
        vid = h.get('id')
        if not vid:
            continue
        key = f'dailymotion:{vid}'
        if key not in dedup:
            dedup[key] = h

    print(f'{len(dedup)} unique candidates after dedupe')

    # Score and filter FIRST (before checking database)
    today = dt.date.today()
    today_s = today.isoformat()

    filtered_candidates = []
    duration_filtered = 0
    score_filtered = 0

    for key, h in dedup.items():
        title = h.get('title', '')
        sid = h.get('__series_id')
        aliases = aliases_by_sid.get(sid, [])
        raw_score = compute_score(title, aliases)
        score = _normalize_score(raw_score, score_scale)

        # Apply filters
        duration = h.get('duration', 0) or 0
        if min_duration_sec > 0 and duration < min_duration_sec:
            duration_filtered += 1
            continue

        if min_score > 0.0 and score < min_score:
            score_filtered += 1
            continue

        # Passed all filters
        filtered_candidates.append({
            'key': key,
            'video': h,
            'raw_score': raw_score,
            'score': score,
            'sid': sid,
            'aliases': aliases
        })

    print(f'After filtering: {len(filtered_candidates)} candidates remain')
    if duration_filtered:
        print(f'  - Duration < {min_duration_sec}s: {duration_filtered}')
    if score_filtered:
        print(f'  - Score < {min_score}: {score_filtered}')

    # Now batch check existing videos (only filtered ones)
    filtered_video_ids = [c['video']['id'] for c in filtered_candidates if c['video'].get('id')]
    print(f'Checking which {len(filtered_video_ids)} videos already exist in database...')
    existing_ids = get_existing_video_ids(filtered_video_ids, platform='dailymotion')
    print(f'Found {len(existing_ids)} existing videos')

    # Prepare final data
    videos_to_insert = []
    rows = []

    for c in filtered_candidates:
        h = c['video']
        raw_score = c['raw_score']
        score = c['score']
        sid = c['sid']
        title = h.get('title', '')
        video_id = h.get('id')
        uploader = h.get('owner.username') or ''

        # Check if new
        is_new = video_id not in existing_ids

        # Prepare for database
        video_data = {
            'platform': 'dailymotion',
            'video_id': video_id,
            'url': h.get('url'),
            'title': title,
            'uploader': uploader,
            'duration_sec': h.get('duration'),
            'publish_time': h.get('created_time'),
            'views': h.get('views_total'),
            'raw_score': round(raw_score, 3),
            'score': round(score, 3),
            'series_id': sid,
            'series_name': titles_by_sid.get(sid, ''),
            'source_term': h.get('__source_term'),
            'geoblocking': [],
            'blocked_regions': [],
        }

        # Only insert new videos to preserve first_seen and avoid unnecessary updates
        if is_new:
            video_data['first_seen'] = today_s
            videos_to_insert.append(video_data)

        # CSV row
        duration = h.get('duration', 0) or 0
        rows.append([
            'dailymotion', video_id, title, h.get('url', ''), uploader,
            str(duration), f"{score:.1f}", 'new' if is_new else 'existing'
        ])

    # Insert to database (upsert: insert new, ignore existing)
    if videos_to_insert:
        print(f'\nInserting {len(videos_to_insert)} videos to database...')
        insert_videos(videos_to_insert)
        print(f'✓ Database updated. Total videos: {count_videos()}')

    # Write CSV reports
    out_csv = os.path.join(out_dir, f'dailymotion_candidates_{today_s}.csv')
    with open(out_csv, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['platform', 'video_id', 'title', 'url', 'uploader', 'duration_sec', 'score', 'status'])
        rows_sorted = sorted(rows, key=lambda r: -float(r[6]) if r[6].replace('.', '').isdigit() else 0)
        w.writerows(rows_sorted)

    print(f'Wrote {out_csv} with {len(rows)} rows')

    # New detections only
    new_rows = [r for r in rows if r[7] == 'new']
    if new_rows:
        new_csv = os.path.join(out_dir, f'new_detections_{today_s}.csv')
        with open(new_csv, 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(['platform', 'video_id', 'title', 'url', 'uploader', 'duration_sec', 'score', 'status'])
            new_sorted = sorted(new_rows, key=lambda r: -float(r[6]) if r[6].replace('.', '').isdigit() else 0)
            w.writerows(new_sorted)
        print(f'Wrote {new_csv} with {len(new_rows)} new detections')


if __name__ == '__main__':
    main()
