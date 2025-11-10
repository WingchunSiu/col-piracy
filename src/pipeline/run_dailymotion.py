#!/usr/bin/env python3
from __future__ import annotations
import csv
import datetime as dt
import json
import os
import time
from typing import Dict, List, Optional, Set

from src.keywords.expand import build_series_keywords
from src.matching.score import compute_score
from src.platforms.dailymotion import search_videos, get_video_status, parse_geoblocking


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
    if score < 0:
        score = 0.0
    if score > 10.0:
        score = 10.0
    return score


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

    per_term_limit = _int_env('DAILYMOTION_PER_TERM_LIMIT', 200)
    primary_aliases = _int_env('DAILYMOTION_PRIMARY_ALIASES', 2, minimum=0)
    primary_per_term_limit = _int_env(
        'DAILYMOTION_PRIMARY_PER_TERM_LIMIT', max(per_term_limit, 1), minimum=1
    )
    sleep_sec = _float_env('DAILYMOTION_SLEEP_SEC', 0.3)
    score_scale = _float_env('DAILYMOTION_SCORE_SCALE', 6.0, minimum=0.1)
    min_duration_sec = _int_env('DAILYMOTION_MIN_DURATION_SEC', 300, minimum=0)
    min_score = _float_env('DAILYMOTION_MIN_SCORE', 5.0, minimum=0.0)

    # Geo-blocking detection config (disabled by default for speed - use recheck_videos.py instead)
    enable_geo_check = _bool_env('DAILYMOTION_ENABLE_GEO_CHECK', False)
    check_regions_raw = os.environ.get('DAILYMOTION_CHECK_REGIONS', 'US,CN')
    check_regions = [r.strip() for r in check_regions_raw.split(',') if r.strip()] if enable_geo_check else []
    geo_sleep_sec = _float_env('DAILYMOTION_GEO_SLEEP_SEC', 0.1)

    # Query Dailymotion
    all_hits: List[Dict] = []
    total_series = len(keywords_by_sid)
    if total_series == 0:
        if series_filter:
            print('No series matched requested DAILYMOTION_SERIES_IDS; exiting.')
        else:
            print('No series available for querying; exiting.')
        return
    print(
        'Searching Dailymotion for '
        f"{total_series} series (primary limit {primary_per_term_limit} for first {primary_aliases} aliases, "
        f"default limit {per_term_limit} per term, sleep {sleep_sec:.2f}s)"
    )
    for idx, (sid, terms) in enumerate(keywords_by_sid.items(), start=1):
        aliases = aliases_by_sid.get(sid, [])
        title_hint = titles_by_sid.get(sid) or (aliases[0] if aliases else sid)
        print(f'[{idx}/{total_series}] {title_hint} -> {len(terms)} terms')
        series_hits: List[Dict] = []
        primary_terms: List[str] = []
        secondary_terms: List[str] = terms
        if primary_aliases > 0:
            primary_terms = terms[:primary_aliases]
            secondary_terms = terms[primary_aliases:]
        if primary_terms:
            series_hits.extend(
                search_videos(primary_terms, per_term_limit=primary_per_term_limit, sleep_sec=sleep_sec)
            )
        if secondary_terms:
            series_hits.extend(
                search_videos(secondary_terms, per_term_limit=per_term_limit, sleep_sec=sleep_sec)
            )
        hits = series_hits
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

    # Geo-blocking check (efficient: uses geoblocking field from API)
    if check_regions:
        print(f'Checking geo-blocking info for new videos')
        checked_count = 0
        for key, h in dedup.items():
            vid = h.get('id')
            if not vid:
                continue

            # Only check geo for new videos (not already in state)
            if key not in prev_state:
                try:
                    status_data = get_video_status(vid)
                    geoblocking = status_data.get('geoblocking', [])
                    blocked_regions, available_regions = parse_geoblocking(geoblocking)

                    h['__geoblocking'] = geoblocking
                    h['__blocked_regions'] = blocked_regions
                    h['__available_regions'] = available_regions
                    checked_count += 1

                    time.sleep(geo_sleep_sec)
                except Exception as e:
                    print(f'  Warning: Failed to check geo for video {vid}: {e}')
                    h['__geoblocking'] = []
                    h['__blocked_regions'] = []
                    h['__available_regions'] = []

        if checked_count > 0:
            print(f'  Geo-checked {checked_count} new videos')

    today = dt.date.today()
    today_s = today.isoformat()

    # Score and filter candidates
    new_state: Dict[str, Dict] = {}
    rows: List[List[str]] = []
    for key, h in dedup.items():
        title = h.get('title', '')
        sid = h.get('__series_id')
        aliases = aliases_by_sid.get(sid, [])
        raw_score = compute_score(title, aliases)
        uploader = h.get('owner.username') or ''
        whitelisted = is_whitelisted(uploader, data)
        if whitelisted:
            raw_score -= 2.0
        if raw_score < 0:
            raw_score = 0.0
        score = _normalize_score(raw_score, score_scale)

        # Apply filters
        duration = h.get('duration', 0) or 0
        if min_duration_sec > 0 and duration < min_duration_sec:
            continue
        if min_score > 0.0 and score < min_score:
            continue

        prev = prev_state.get(key)
        is_new = prev is None
        first_seen = prev.get('first_seen') if prev else today_s

        new_state[key] = {
            'platform': 'dailymotion',
            'video_id': h.get('id'),
            'url': h.get('url'),
            'title': title,
            'uploader': uploader,
            'duration_sec': h.get('duration'),
            'publish_time': h.get('created_time'),
            'views': h.get('views_total'),
            'raw_score': round(raw_score, 3),
            'score': round(score, 3),
            'series_id': sid,
            'first_seen': first_seen,
            'source_term': h.get('__source_term'),
            'is_new': is_new,
            'geoblocking': h.get('__geoblocking', []) if is_new else prev.get('geoblocking', []),
            'blocked_regions': h.get('__blocked_regions', []) if is_new else prev.get('blocked_regions', []),
        }
        # Geo status summary
        if is_new and check_regions:
            blocked_regions = h.get('__blocked_regions', [])
        else:
            # For existing videos, use previous geo data
            blocked_regions = prev.get('blocked_regions', []) if prev else []

        # Determine geo_status
        if not check_regions:
            geo_status = 'N/A'
        elif blocked_regions:
            geo_status = f"{','.join(blocked_regions)}屏蔽"
        else:
            geo_status = '全球可见'

        rows.append([
            'dailymotion', h.get('id', ''), title, h.get('url', ''), uploader,
            str(h.get('duration', '')),
            f"{score:.1f}",
            'new' if is_new else 'existing',
            geo_status
        ])

    # Carry over previously seen videos that weren't re-detected today
    # They stay in state but won't appear in today's CSV (recheck will handle them)
    seen_keys = set(new_state.keys())
    for key, prev in prev_state.items():
        if key not in seen_keys:
            new_state[key] = prev

    # Write state
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(new_state, f, ensure_ascii=False, indent=2)

    # Write full report CSV (all videos found today)
    out_csv = os.path.join(out_dir, f'dailymotion_candidates_{today_s}.csv')
    with open(out_csv, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['platform', 'video_id', 'title', 'url', 'uploader', 'duration_sec', 'score', 'status', 'geo_status'])
        # Sort: score desc
        def sort_key(r):
            try:
                score_val = float(r[6])
            except Exception:
                score_val = 0.0
            return -score_val
        for r in sorted(rows, key=sort_key):
            w.writerow(r)

    print(f'Wrote {out_csv} with {len(rows)} rows')

    # Write new detections report (only new videos for operations team)
    new_rows = [r for r in rows if r[7] == 'new']  # status column (now index 7)
    if new_rows:
        new_csv = os.path.join(out_dir, f'new_detections_{today_s}.csv')
        with open(new_csv, 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(['platform', 'video_id', 'title', 'url', 'uploader', 'duration_sec', 'score', 'status', 'geo_status'])
            for r in sorted(new_rows, key=sort_key):
                w.writerow(r)
        print(f'Wrote {new_csv} with {len(new_rows)} new detections (for operations team)')


if __name__ == '__main__':
    main()
