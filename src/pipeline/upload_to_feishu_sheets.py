#!/usr/bin/env python3
"""
Upload CSV reports to Feishu Sheets.

Creates new sheets for each day's reports in a single spreadsheet.
Uses Feishu Sheets API v3.
"""
from __future__ import annotations
import csv
import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import date
from typing import Dict, List, Any


def _make_request(url: str, token: str, data: Dict = None, method: str = 'POST', retries: int = 3) -> Dict:
    """Make HTTP request with retry logic."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json; charset=utf-8'
    }

    for attempt in range(retries):
        try:
            if data:
                request_data = json.dumps(data).encode('utf-8')
                req = urllib.request.Request(url, data=request_data, headers=headers, method=method)
            else:
                req = urllib.request.Request(url, headers=headers, method=method)

            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                return result

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ''
            print(f"  HTTP {e.code} error (attempt {attempt + 1}/{retries}): {error_body}")

            if e.code == 429:  # Rate limit
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"  Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            elif e.code >= 500:  # Server error
                if attempt < retries - 1:
                    time.sleep(1)
                    continue
            raise

        except Exception as e:
            print(f"  Request failed (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(1)
                continue
            raise

    raise Exception(f"Failed after {retries} attempts")


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """Get tenant access token for Feishu API."""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = {
        "app_id": app_id,
        "app_secret": app_secret
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        if result.get('code') != 0:
            raise Exception(f"Failed to get token: {result}")
        return result['tenant_access_token']


def add_sheet_to_spreadsheet(token: str, spreadsheet_token: str, title: str) -> str:
    """
    Add a new sheet to the spreadsheet using v3 API.

    API: POST /open-apis/sheets/v3/spreadsheets/:spreadsheet_token/sheets_v3
    Returns sheet_id.
    """
    url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet_token}/sheets_v3"

    data = {
        "title": title,
        "index": 0  # Add at the beginning
    }

    result = _make_request(url, token, data)

    if result.get('code') != 0:
        raise Exception(f"Failed to add sheet: {result}")

    # Extract sheet_id from response
    sheet_id = result.get('data', {}).get('sheet', {}).get('sheet_id')
    if not sheet_id:
        raise Exception(f"No sheet_id in response: {result}")

    return sheet_id


def write_csv_to_sheet(token: str, spreadsheet_token: str, sheet_id: str, csv_path: str):
    """
    Write CSV data to a Feishu sheet using v3 API.

    API: POST /open-apis/sheets/v3/spreadsheets/:spreadsheet_token/values_append
    Data format: [[cell1, cell2, ...], [row2_cell1, row2_cell2, ...]]
    """
    # Read CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        print(f"Warning: {csv_path} is empty")
        return

    # Feishu v3 API expects simple 2D array format
    # Convert CSV rows to the format expected by API
    # API expects: {"values": [["A1", "B1"], ["A2", "B2"]]}

    # Write data in chunks (API limit: 5000 rows per request)
    chunk_size = 5000
    total_rows = len(rows)

    for i in range(0, total_rows, chunk_size):
        chunk = rows[i:i+chunk_size]

        # Calculate range (A1 notation)
        # For appending, we can use the sheet_id directly
        # If this is the first chunk, we want to start from A1
        start_row = i + 1
        end_row = start_row + len(chunk) - 1

        # Determine number of columns
        max_cols = max(len(row) for row in chunk) if chunk else 0
        end_col_letter = _number_to_column_letter(max_cols)

        range_notation = f"{sheet_id}!A{start_row}:{end_col_letter}{end_row}"

        url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet_token}/values_prepend"

        # For the first chunk, use prepend to start from A1
        # For subsequent chunks, use append
        if i == 0:
            url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet_token}/values_prepend"
        else:
            url = f"https://open.feishu.cn/open-apis/sheets/v3/spreadsheets/{spreadsheet_token}/values_append"

        data = {
            "valueRange": {
                "range": range_notation,
                "values": chunk
            }
        }

        result = _make_request(url, token, data)

        if result.get('code') != 0:
            raise Exception(f"Failed to write data (chunk {i//chunk_size + 1}): {result}")

        print(f"  Written {len(chunk)} rows (chunk {i//chunk_size + 1}/{(total_rows + chunk_size - 1)//chunk_size})")

        # Small delay between chunks to avoid rate limiting
        if i + chunk_size < total_rows:
            time.sleep(0.5)


def _number_to_column_letter(n: int) -> str:
    """Convert column number to letter (1=A, 27=AA, etc.)."""
    result = ""
    while n > 0:
        n -= 1
        result = chr(65 + (n % 26)) + result
        n //= 26
    return result or "A"


def send_notification_card(webhook_url: str, spreadsheet_url: str,
                          new_count: int, status_count: int, today_str: str):
    """Send notification card to Feishu group via webhook."""
    card_content = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "📊 每日盗版检测报告"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**日期**: {today_str}\n**新检测**: {new_count} 个视频\n**状态更新**: {status_count} 个视频"
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "📊 查看在线表格"
                            },
                            "type": "primary",
                            "url": spreadsheet_url
                        }
                    ]
                }
            ]
        }
    }

    data = json.dumps(card_content).encode('utf-8')
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            if result.get('code') != 0:
                print(f"Warning: Failed to send notification: {result}")
            else:
                print('✓ Notification sent')
    except Exception as e:
        print(f"Warning: Failed to send notification: {e}")


def main():
    # Config from environment
    app_id = os.environ.get('FEISHU_APP_ID')
    app_secret = os.environ.get('FEISHU_APP_SECRET')
    spreadsheet_token = os.environ.get('FEISHU_SPREADSHEET_TOKEN')
    webhook_url = os.environ.get('FEISHU_WEBHOOK')

    if not all([app_id, app_secret, spreadsheet_token]):
        print("Error: Missing required environment variables:")
        print("  FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_SPREADSHEET_TOKEN")
        sys.exit(1)

    today_str = date.today().isoformat()
    report_dir = os.environ.get('REPORT_DIR', 'reports')

    new_detections_csv = os.path.join(report_dir, f'new_detections_{today_str}.csv')
    status_update_csv = os.path.join(report_dir, f'status_update_{today_str}.csv')

    # Check if reports exist
    if not os.path.exists(new_detections_csv):
        print(f"Error: {new_detections_csv} not found")
        sys.exit(1)

    if not os.path.exists(status_update_csv):
        print(f"Error: {status_update_csv} not found")
        sys.exit(1)

    print('Getting Feishu access token...')
    token = get_tenant_access_token(app_id, app_secret)
    print('✓ Token acquired')

    # Create two sheets for today
    print(f'\nCreating sheets for {today_str}...')
    new_detections_title = f"{today_str} 新检测"
    status_update_title = f"{today_str} 状态追踪"

    try:
        new_sheet_id = add_sheet_to_spreadsheet(token, spreadsheet_token, new_detections_title)
        print(f'✓ Created sheet: {new_detections_title} (ID: {new_sheet_id})')
    except Exception as e:
        print(f'Error creating new detections sheet: {e}')
        sys.exit(1)

    try:
        status_sheet_id = add_sheet_to_spreadsheet(token, spreadsheet_token, status_update_title)
        print(f'✓ Created sheet: {status_update_title} (ID: {status_sheet_id})')
    except Exception as e:
        print(f'Error creating status update sheet: {e}')
        sys.exit(1)

    # Write data to sheets
    print('\nWriting new detections data...')
    try:
        write_csv_to_sheet(token, spreadsheet_token, new_sheet_id, new_detections_csv)
        print('✓ New detections data written')
    except Exception as e:
        print(f'Error writing new detections: {e}')
        sys.exit(1)

    print('\nWriting status update data...')
    try:
        write_csv_to_sheet(token, spreadsheet_token, status_sheet_id, status_update_csv)
        print('✓ Status update data written')
    except Exception as e:
        print(f'Error writing status update: {e}')
        sys.exit(1)

    # Count records
    with open(new_detections_csv, 'r', encoding='utf-8') as f:
        new_count = sum(1 for _ in f) - 1  # Exclude header

    with open(status_update_csv, 'r', encoding='utf-8') as f:
        status_count = sum(1 for _ in f) - 1

    print(f'\n{"="*50}')
    print(f'✓ Upload completed successfully')
    print(f'  New detections: {new_count} videos')
    print(f'  Status updates: {status_count} videos')
    print(f'{"="*50}')

    # Send notification if webhook is configured
    if webhook_url:
        spreadsheet_url = f"https://bytedance.feishu.cn/sheets/{spreadsheet_token}"
        print('\nSending notification to Feishu group...')
        send_notification_card(webhook_url, spreadsheet_url,
                             new_count, status_count, today_str)
    else:
        print('\nNote: FEISHU_WEBHOOK not set, skipping notification')


if __name__ == '__main__':
    main()
