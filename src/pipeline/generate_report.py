#!/usr/bin/env python3
"""Generate combined Excel report with two sheets."""
import os
import sys
from datetime import date
import pandas as pd


def generate_combined_report(today: str = None):
    """Generate Excel report with new_detections and status_update sheets."""
    if today is None:
        today = date.today().isoformat()

    report_dir = os.environ.get('REPORT_DIR', 'reports')

    new_detections_path = os.path.join(report_dir, f'new_detections_{today}.csv')
    status_update_path = os.path.join(report_dir, f'status_update_{today}.csv')
    output_path = os.path.join(report_dir, f'piracy_report_{today}.xlsx')

    # Check if source files exist
    if not os.path.exists(new_detections_path):
        print(f'❌ {new_detections_path} not found')
        return False

    if not os.path.exists(status_update_path):
        print(f'❌ {status_update_path} not found')
        return False

    # Read CSVs
    print(f'Reading {new_detections_path}...')
    new_detections = pd.read_csv(new_detections_path)

    print(f'Reading {status_update_path}...')
    status_update = pd.read_csv(status_update_path)

    # Create Excel with two sheets
    print(f'Creating {output_path}...')
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        new_detections.to_excel(writer, sheet_name='新检测视频', index=False)
        status_update.to_excel(writer, sheet_name='状态追踪', index=False)

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
    print(f'  - Sheet 1 (新检测视频): {len(new_detections)} rows')
    print(f'  - Sheet 2 (状态追踪): {len(status_update)} rows')

    return True


if __name__ == '__main__':
    if len(sys.argv) > 1:
        success = generate_combined_report(sys.argv[1])
    else:
        success = generate_combined_report()

    sys.exit(0 if success else 1)
