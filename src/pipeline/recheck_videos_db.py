#!/usr/bin/env python3
"""Recheck video status using Supabase database."""
import csv
import datetime as dt
import os
import time

from src.platforms.dailymotion import get_video_status
from src.database.supabase_db import (
    get_videos_to_recheck,
    update_video_status,
    get_all_videos_for_report,
    count_videos
)


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
    """Infer action needed based on status and time."""
    if api_status == 'removed':
        return '已下架 ✓'
    elif api_status == 'private':
        return '已变私密 ✓'
    elif api_status == 'password_protected':
        return '已加密码保护 ✓'
    elif api_status == 'rejected':
        return '被平台拒绝 ✓'
    elif api_status == 'active':
        if days_since_detection >= 7:
            return '需要催办 ⚠️'
        elif days_since_detection >= 2:
            return '假设已举报，等待处理'
        else:
            return '需要举报'
    return f"未知状态({api_status})"


def main():
    out_dir = os.environ.get('REPORT_DIR', 'reports')
    os.makedirs(out_dir, exist_ok=True)

    recheck_min_days = _int_env('DAILYMOTION_RECHECK_MIN_DAYS', 2)
    recheck_max_days = _int_env('DAILYMOTION_RECHECK_MAX_DAYS', 30)
    sleep_sec = _float_env('DAILYMOTION_RECHECK_SLEEP_SEC', 0.2)

    # Get videos to recheck (between 2-30 days old, active status)
    videos = get_videos_to_recheck(min_days=recheck_min_days, max_days=recheck_max_days)

    if not videos:
        print(f'No videos to recheck (range: {recheck_min_days}-{recheck_max_days} days)')
        return

    print(f'Rechecking {len(videos)} videos (days {recheck_min_days}-{recheck_max_days})...')

    # Recheck each video
    errors = []
    for idx, video in enumerate(videos, 1):
        video_id = video['video_id']
        platform = video['platform']

        if idx % 10 == 0:
            print(f'  Progress: {idx}/{len(videos)}')

        try:
            response = get_video_status(video_id)

            # Determine status
            if not response.get('exists'):
                status = 'removed'
            elif response.get('private'):
                status = 'private'
            elif response.get('password_protected'):
                status = 'password_protected'
            elif response.get('status') == 'rejected':
                status = 'rejected'
            else:
                status = 'active'

            # Update database
            update_video_status(video_id, status, platform)

            time.sleep(sleep_sec)

        except Exception as e:
            errors.append((video_id, str(e)))

    print(f'Recheck completed')

    if errors:
        print(f'\n⚠️  {len(errors)} videos failed:')
        for vid, err in errors[:5]:
            print(f'  {vid}: {err}')
        if len(errors) > 5:
            print(f'  ... and {len(errors) - 5} more')

    # Generate status report (all videos within max_days, including removed)
    print(f'\nGenerating status report...')
    today = dt.date.today()
    all_videos = get_all_videos_for_report(max_days=recheck_max_days, include_ignored=False)

    rows = []
    for video in all_videos:
        first_seen_str = video.get('first_seen')
        if not first_seen_str:
            continue

        try:
            first_seen = dt.date.fromisoformat(str(first_seen_str))
            days_tracked = (today - first_seen).days
        except ValueError:
            days_tracked = 0

        api_status = video.get('api_status') or 'unknown'
        action_needed = infer_action_needed(api_status, days_tracked)

        rows.append([
            video.get('platform', 'dailymotion'),
            video.get('video_id', ''),
            video.get('title', ''),
            video.get('url', ''),
            video.get('uploader', ''),
            first_seen_str,
            str(days_tracked),
            api_status,
            video.get('api_last_checked', ''),
            action_needed,
        ])

    # Write report
    report_path = os.path.join(out_dir, f'status_update_{today.isoformat()}.csv')
    with open(report_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow([
            'platform', 'video_id', 'title', 'url', 'uploader',
            'first_seen', 'days_tracked', 'api_status',
            'last_checked', 'action_needed'
        ])

        # Sort by priority
        def sort_key(r):
            action = r[9]
            days_tracked = int(r[6]) if r[6].isdigit() else 0

            if '催办' in action:
                priority = 0
            elif '举报' in action:
                priority = 1
            elif '下架' in action:
                priority = 3
            else:
                priority = 2

            return (priority, -days_tracked)

        w.writerows(sorted(rows, key=sort_key))

    print(f'Status report written to {report_path} with {len(rows)} videos')
    print(f'Total videos in database: {count_videos()}')


if __name__ == '__main__':
    main()
