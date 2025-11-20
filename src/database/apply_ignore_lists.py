#!/usr/bin/env python3
"""Mark videos as ignored based on a CSV list (e.g., 追踪表需删除链接)."""
import argparse
import csv
from typing import List

from src.database.supabase_db import set_ignore_reason


def load_video_ids(path: str) -> List[str]:
    """Read video IDs from CSV. Expects a column named 视频ID or second column."""
    video_ids = []
    with open(path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        rows = list(reader)
        if not rows:
            return video_ids
        header = rows[0]
        body = rows[1:] if any(header) else rows

        column_idx = None
        for idx, col in enumerate(header):
            if str(col).strip() in ('视频ID', 'video_id', '视频id'):
                column_idx = idx
                break
        if column_idx is None:
            column_idx = 1 if len(header) > 1 else 0

        for row in body:
            if len(row) <= column_idx:
                continue
            vid = str(row[column_idx]).strip()
            if vid:
                video_ids.append(vid)
    return video_ids


def main():
    parser = argparse.ArgumentParser(description="Mark videos as ignored using a CSV list.")
    parser.add_argument('csv_path', help='Path to CSV (e.g., data/追踪表需删除链接 - Sheet1.csv)')
    parser.add_argument('--platform', default='dailymotion', help='Platform name (default: dailymotion)')
    parser.add_argument('--reason', default='manual_ignore', help='Ignore reason flag to set')
    parser.add_argument('--dry-run', action='store_true', help='Only print counts, do not update database')
    args = parser.parse_args()

    video_ids = load_video_ids(args.csv_path)
    print(f'Loaded {len(video_ids)} video IDs from {args.csv_path}')

    if not video_ids:
        return

    if args.dry_run:
        print('Dry run: no updates sent.')
        return

    updated = set_ignore_reason(video_ids, reason=args.reason, platform=args.platform)
    print(f'✓ Marked {updated} videos with ignore_reason={args.reason}')


if __name__ == '__main__':
    main()
