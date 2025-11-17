#!/usr/bin/env python3
"""Generate Excel report from database with two sheets."""
import os
import sys
from datetime import date, timedelta
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.supabase_db import get_client, delete_removed_videos, count_videos


def _compute_status(api_status: str) -> str:
    """Compute human-readable status."""
    if api_status in ('removed', 'private', 'password_protected', 'rejected'):
        return '已下架 ✓'
    return '未下架'


def generate_report_from_db(report_date: str = None, tracking_days: int = 30):
    """
    Generate Excel report with two sheets:
    1. 今日新检测 (new detections today)
    2. 往期追踪 (past videos within tracking_days, with status)

    After generating report, deletes removed videos from database.
    """
    if report_date is None:
        report_date = date.today().isoformat()

    today = date.fromisoformat(report_date)
    cutoff_date = (today - timedelta(days=tracking_days)).isoformat()

    report_dir = os.environ.get('REPORT_DIR', 'reports')
    os.makedirs(report_dir, exist_ok=True)

    output_path = os.path.join(report_dir, f'piracy_report_{report_date}.xlsx')

    client = get_client()

    # Sheet 1: 今日新检测 (videos detected today)
    # Use pagination to handle >1000 new detections
    print(f'Fetching new detections for {report_date}...')
    new_detections = []
    offset = 0
    page_size = 1000

    while True:
        response = client.table('videos') \
            .select('*') \
            .eq('first_seen', report_date) \
            .order('score', desc=True) \
            .range(offset, offset + page_size - 1) \
            .execute()

        if not response.data:
            break

        new_detections.extend(response.data)
        offset += page_size

        if len(response.data) < page_size:
            break

    print(f'  Found {len(new_detections)} new detections')

    # Sheet 2: 往期追踪 (all videos within tracking window, including removed)
    # Use pagination to handle >1000 videos
    print(f'Fetching videos from past {tracking_days} days...')
    all_videos = []
    offset = 0

    while True:
        response = client.table('videos') \
            .select('*') \
            .gte('first_seen', cutoff_date) \
            .lt('first_seen', report_date) \
            .order('first_seen', desc=True) \
            .range(offset, offset + page_size - 1) \
            .execute()

        if not response.data:
            break

        all_videos.extend(response.data)
        offset += page_size

        if len(response.data) < page_size:
            break

    print(f'  Found {len(all_videos)} videos in tracking window')

    # Process Sheet 1: 今日新检测
    sheet1_data = []
    for video in new_detections:
        sheet1_data.append({
            '平台': video.get('platform', 'dailymotion'),
            '视频ID': video.get('video_id', ''),
            '标题': video.get('title', ''),
            'URL': video.get('url', ''),
            '上传者': video.get('uploader', ''),
            '时长(秒)': video.get('duration_sec', ''),
            '分数': round(video.get('score', 0), 1),
            '检测时间': video.get('first_seen', ''),
            '剧集ID': video.get('series_id', '')
        })

    # Process Sheet 2: 往期追踪
    sheet2_data = []
    for video in all_videos:
        first_seen_str = video.get('first_seen')
        if first_seen_str:
            try:
                first_seen = date.fromisoformat(str(first_seen_str))
                days_tracked = (today - first_seen).days
            except ValueError:
                days_tracked = 0
        else:
            days_tracked = 0

        api_status = video.get('api_status') or 'active'
        status = _compute_status(api_status)

        sheet2_data.append({
            '平台': video.get('platform', 'dailymotion'),
            '视频ID': video.get('video_id', ''),
            '标题': video.get('title', ''),
            'URL': video.get('url', ''),
            '上传者': video.get('uploader', ''),
            '首次检测': video.get('first_seen', ''),
            '追踪天数': days_tracked,
            '当前状态': status,
            '上次检查': video.get('api_last_checked', ''),
            '剧集ID': video.get('series_id', '')
        })

    # Sort sheet2: 未下架 first, then by days_tracked (desc)
    sheet2_data.sort(key=lambda x: (x['当前状态'] == '已下架 ✓', -x['追踪天数']))

    # Create DataFrames
    df_new = pd.DataFrame(sheet1_data)
    df_tracking = pd.DataFrame(sheet2_data)

    # Create Excel with two sheets
    print(f'Creating {output_path}...')
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_new.to_excel(writer, sheet_name='今日新检测', index=False)
        df_tracking.to_excel(writer, sheet_name='往期追踪', index=False)

        # Auto-adjust column widths
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column = [cell for cell in column]
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column[0].column_letter].width = adjusted_width

    print(f'✓ Report generated: {output_path}')
    print(f'  - Sheet 1 (今日新检测): {len(df_new)} rows')
    print(f'  - Sheet 2 (往期追踪): {len(df_tracking)} rows')

    # Cleanup: delete removed videos from database
    print(f'\nCleaning up removed videos from database...')
    removed_count = delete_removed_videos()
    if removed_count > 0:
        print(f'✓ Deleted {removed_count} removed videos')
    else:
        print('No removed videos to delete')

    print(f'Total videos remaining in database: {count_videos()}')

    return True


if __name__ == '__main__':
    if len(sys.argv) > 1:
        success = generate_report_from_db(sys.argv[1])
    else:
        success = generate_report_from_db()

    sys.exit(0 if success else 1)
