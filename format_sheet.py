"""
Beautiful Google Sheet Formatter for Daily Routine Tracker
- Proper design with colors
- Data validation for tick/cross selection
- Progress bars
- Correct column widths
"""

import gspread
from google.oauth2.service_account import Credentials
import json
import os

# Configuration
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), 'service-account.json')
DATA_FILE = os.path.join(os.path.dirname(__file__), 'tracker_data.json')
SHEET_ID = '1_kJ8RfV_W7Djoh531-l38GGDATtu2vXV7Fa8XGW7HWE'

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def load_data():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_and_sync_sheet():
    print("🔧 Connecting to Google Sheets...")
    
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)
    
    # Get or create main sheet
    try:
        sheet = spreadsheet.worksheet("January 2026")
    except:
        sheet = spreadsheet.sheet1
        sheet.update_title("January 2026")
    
    print("📊 Loading local data...")
    data = load_data()
    
    # Remove any DAILY TOTALS entries from habits
    data['habits'] = [h for h in data['habits'] if 'DAILY TOTALS' not in h.get('name', '')]
    
    # Clear sheet completely
    sheet.clear()
    
    # Clear all conditional formatting
    spreadsheet.batch_update({
        "requests": [{
            "deleteConditionalFormatRule": {
                "sheetId": sheet.id,
                "index": 0
            }
        }]
    })
    
    dates = data['dates']
    habits = data['habits']
    
    print(f"📝 Writing {len(habits)} habits...")
    
    # Create header row
    headers = ["📋 Habit"] + dates + ["✓ Done", "✗ Miss", "📊 Progress", "🔥 Streak"]
    
    # Data rows
    all_rows = [headers]
    
    for habit in habits:
        row = [habit['name']]
        completed = 0
        missed = 0
        streak = 0
        counting = True
        
        for date in dates:
            status = habit['daily_status'].get(date, '')
            row.append(status)
            if status == '✓':
                completed += 1
                if counting:
                    streak += 1
            elif status == '✗':
                missed += 1
                counting = False
        
        total = completed + missed
        progress = round((completed / total * 100) if total > 0 else 0)
        row.extend([completed, missed, f"{progress}%", streak])
        all_rows.append(row)
    
    # Write data
    sheet.update(values=all_rows, range_name='A1')
    
    print("🎨 Applying beautiful formatting...")
    
    # Freeze header row and habit column
    sheet.freeze(rows=1, cols=1)
    
    # Calculate column letters
    num_cols = len(headers)
    last_col = chr(ord('A') + num_cols - 1) if num_cols <= 26 else 'AK'
    num_rows = len(all_rows)
    
    # Format header row - Purple gradient
    sheet.format(f'A1:{last_col}1', {
        'backgroundColor': {'red': 0.55, 'green': 0.36, 'blue': 0.96},
        'textFormat': {
            'bold': True,
            'fontSize': 10,
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}
        },
        'horizontalAlignment': 'CENTER',
        'verticalAlignment': 'MIDDLE'
    })
    
    # Format habit column - Dark background
    sheet.format(f'A2:A{num_rows}', {
        'backgroundColor': {'red': 0.12, 'green': 0.12, 'blue': 0.18},
        'textFormat': {
            'bold': True,
            'fontSize': 10,
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}
        },
        'horizontalAlignment': 'LEFT',
        'verticalAlignment': 'MIDDLE'
    })
    
    # Format date cells - Center aligned
    date_end_col = chr(ord('A') + len(dates))
    sheet.format(f'B2:{date_end_col}{num_rows}', {
        'horizontalAlignment': 'CENTER',
        'verticalAlignment': 'MIDDLE',
        'textFormat': {
            'fontSize': 12,
            'bold': True
        }
    })
    
    # Format summary columns (Total Done, Miss, Progress, Streak)
    summary_start = chr(ord('A') + len(dates) + 1)
    sheet.format(f'{summary_start}2:{last_col}{num_rows}', {
        'backgroundColor': {'red': 0.15, 'green': 0.15, 'blue': 0.2},
        'horizontalAlignment': 'CENTER',
        'verticalAlignment': 'MIDDLE',
        'textFormat': {
            'bold': True,
            'foregroundColor': {'red': 0.8, 'green': 0.8, 'blue': 1}
        }
    })
    
    # Set column widths
    requests = []
    
    # Habit column - wider
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet.id,
                "dimension": "COLUMNS",
                "startIndex": 0,
                "endIndex": 1
            },
            "properties": {"pixelSize": 180},
            "fields": "pixelSize"
        }
    })
    
    # Date columns - narrow
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet.id,
                "dimension": "COLUMNS",
                "startIndex": 1,
                "endIndex": len(dates) + 1
            },
            "properties": {"pixelSize": 55},
            "fields": "pixelSize"
        }
    })
    
    # Summary columns - medium
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet.id,
                "dimension": "COLUMNS",
                "startIndex": len(dates) + 1,
                "endIndex": len(headers)
            },
            "properties": {"pixelSize": 70},
            "fields": "pixelSize"
        }
    })
    
    # Row height
    requests.append({
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet.id,
                "dimension": "ROWS",
                "startIndex": 0,
                "endIndex": num_rows
            },
            "properties": {"pixelSize": 30},
            "fields": "pixelSize"
        }
    })
    
    # Conditional formatting for ✓ (green) and ✗ (red)
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet.id,
                    "startRowIndex": 1,
                    "endRowIndex": num_rows,
                    "startColumnIndex": 1,
                    "endColumnIndex": len(dates) + 1
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_EQ",
                        "values": [{"userEnteredValue": "✓"}]
                    },
                    "format": {
                        "backgroundColor": {"red": 0.13, "green": 0.55, "blue": 0.13},
                        "textFormat": {
                            "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                            "bold": True
                        }
                    }
                }
            },
            "index": 0
        }
    })
    
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": sheet.id,
                    "startRowIndex": 1,
                    "endRowIndex": num_rows,
                    "startColumnIndex": 1,
                    "endColumnIndex": len(dates) + 1
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_EQ",
                        "values": [{"userEnteredValue": "✗"}]
                    },
                    "format": {
                        "backgroundColor": {"red": 0.8, "green": 0.2, "blue": 0.2},
                        "textFormat": {
                            "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                            "bold": True
                        }
                    }
                }
            },
            "index": 1
        }
    })
    
    # Data validation for tick/cross dropdown
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 1,
                "endRowIndex": num_rows,
                "startColumnIndex": 1,
                "endColumnIndex": len(dates) + 1
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [
                        {"userEnteredValue": "✓"},
                        {"userEnteredValue": "✗"},
                        {"userEnteredValue": ""}
                    ]
                },
                "showCustomUi": True,
                "strict": False
            }
        }
    })
    
    # Apply all requests
    spreadsheet.batch_update({"requests": requests})
    
    print("✅ Sheet formatted beautifully!")
    print(f"🔗 https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    print("\n📋 Features:")
    print("   ✓ Purple header with white text")
    print("   ✓ Green cells for completed (✓)")
    print("   ✓ Red cells for missed (✗)")
    print("   ✓ Dropdown to select ✓ or ✗")
    print("   ✓ Progress % and Streak columns")
    print("   ✓ Proper column widths")

if __name__ == '__main__':
    format_and_sync_sheet()
