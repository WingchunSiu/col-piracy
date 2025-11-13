#!/usr/bin/env python3
"""
Recheck status of known pirated videos.

Queries the Dailymotion API directly for each video ID in state
to determine current status (removed, private, geo-blocked, etc.)
"""
from __future__ import annotations
import csv
import datetime as dt
import json
import os
import time
from typing import Dict, List

from src.platforms.dailymotion import get_video_status, parse_geoblocking


def _int_env(name: str, default: int) -> int:
    val = os.environ.get(name)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    val = os.environ.get(name)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        return default


def infer_action_needed(api_status: str, days_since_detection: int) -> str:
    """
    Infer what action is needed based on video status and time.

    Args:
        api_status: Video API status (removed/private/active/etc.)
        days_since_detection: Days since first_seen

    Returns:
        Action description in Chinese
    """
    # Successfully handled cases
    if api_status == 'removed':
        return '已下架 ✓'
    elif api_status == 'private':
        return '已变私密 ✓'
    elif api_status == 'password_protected':
        return '已加密码保护 ✓'
    elif api_status == 'rejected':
        return '被平台拒绝 ✓'

    # Active video - still needs action
    elif api_status == 'active':
        if days_since_detection >= 7:
            return '需要催办 ⚠️'
        elif days_since_detection >= 2:
            return '假设已举报，等待处理'
        else:
            return '需要举报'

    # Unknown status
    return f"未知状态({api_status})"


def main():
    # Config
    state_dir = os.environ.get('STATE_DIR', 'state')
    out_dir = os.environ.get('REPORT_DIR', 'reports')
    state_path = os.path.join(state_dir, 'dailymotion_videos.json')

    recheck_days = _int_env('DAILYMOTION_RECHECK_DAYS', 30)
    sleep_sec = _float_env('DAILYMOTION_RECHECK_SLEEP_SEC', 0.5)

    # Load state
    if not os.path.exists(state_path):
        print(f'No state file found at {state_path}')
        return

    with open(state_path, 'r', encoding='utf-8') as f:
        state: Dict[str, Dict] = json.load(f)

    today = dt.date.today()
    today_s = today.isoformat()

    # Filter videos to recheck (only recent ones)
    videos_to_check = {}
    for key, video_info in state.items():
        first_seen_str = video_info.get('first_seen')
        if not first_seen_str:
            continue

        try:
            first_seen = dt.date.fromisoformat(str(first_seen_str))
            days_since = (today - first_seen).days

            if days_since <= recheck_days:
                videos_to_check[key] = video_info
        except ValueError:
            # Invalid date format, skip
            continue

    if not videos_to_check:
        print(f'No videos to recheck (filter: last {recheck_days} days)')
        return

    print(f'Rechecking {len(videos_to_check)} videos detected within last {recheck_days} days')

    # Recheck each video
    errors = []
    for idx, (key, video_info) in enumerate(videos_to_check.items(), 1):
        video_id = video_info.get('video_id')
        if not video_id:
            continue

        if idx % 10 == 0:
            print(f'  Progress: {idx}/{len(videos_to_check)}')

        try:
            # Get video status from API
            response = get_video_status(video_id)

            # Update state based on API response
            if not response.get('exists'):
                video_info['api_status'] = 'removed'
                video_info['geoblocking'] = []
                video_info['blocked_regions'] = []
            elif response.get('private'):
                video_info['api_status'] = 'private'
            elif response.get('password_protected'):
                video_info['api_status'] = 'password_protected'
            elif response.get('status') == 'rejected':
                video_info['api_status'] = 'rejected'
            else:
                video_info['api_status'] = 'active'

            # Skip geo-blocking check (too slow and not needed for daily reports)

            # Update last checked time
            video_info['api_last_checked'] = today_s

            time.sleep(sleep_sec)

        except Exception as e:
            errors.append((video_id, str(e)))
            continue

    print(f'Recheck completed')

    # Show errors if any
    if errors:
        print(f'\n⚠️  {len(errors)} videos failed to recheck:')
        for vid, err in errors[:10]:
            print(f'  {vid}: {err}')
        if len(errors) > 10:
            print(f'  ... and {len(errors) - 10} more')

    # Save updated state
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print(f'Updated state saved to {state_path}')

    # Generate status report
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, f'status_update_{today_s}.csv')

    rows = []
    for key, video_info in state.items():
        first_seen_str = video_info.get('first_seen')
        if not first_seen_str:
            continue

        try:
            first_seen = dt.date.fromisoformat(str(first_seen_str))
            days_tracked = (today - first_seen).days
        except ValueError:
            days_tracked = 0

        api_status = video_info.get('api_status', 'unknown')
        action_needed = infer_action_needed(api_status, days_tracked)

        rows.append([
            video_info.get('platform', 'dailymotion'),
            video_info.get('video_id', ''),
            video_info.get('title', ''),
            video_info.get('url', ''),
            video_info.get('uploader', ''),
            first_seen_str,
            str(days_tracked),
            api_status,
            video_info.get('api_last_checked', ''),
            action_needed,
        ])

    # Write report
    with open(report_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow([
            'platform', 'video_id', 'title', 'url', 'uploader',
            'first_seen', 'days_tracked', 'api_status',
            'last_checked', 'action_needed'
        ])

        # Sort by action priority (needs followup first, then by days tracked)
        def sort_key(r):
            action = r[9]  # action_needed column
            days_tracked = int(r[6]) if r[6].isdigit() else 0

            # Priority order
            if '催办' in action:
                priority = 0
            elif '举报' in action:
                priority = 1
            elif '屏蔽' in action:
                priority = 2
            elif '下架' in action:
                priority = 3
            else:
                priority = 4

            return (priority, -days_tracked)

        for r in sorted(rows, key=sort_key):
            w.writerow(r)

    print(f'Status report written to {report_path} with {len(rows)} videos')


if __name__ == '__main__':
    main()
