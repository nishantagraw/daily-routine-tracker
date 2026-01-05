"""
Create Google Sheet EXACTLY like the image - Clean Habit Tracker
"""
import gspread
from google.oauth2.service_account import Credentials
import json

SHEET_ID = '1_kJ8RfV_W7Djoh531-l38GGDATtu2vXV7Fa8XGW7HWE'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def setup_clean_tracker():
    # Load data
    with open('tracker_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Remove any DAILY TOTALS
    habits = [h for h in data['habits'] if 'TOTAL' not in h.get('name', '').upper()]
    dates = data['dates'][:27]  # Jan 5-31
    
    # Connect
    creds = Credentials.from_service_account_file('service-account.json', scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SHEET_ID)
    sheet = spreadsheet.sheet1
    
    print('🧹 Clearing sheet completely...')
    sheet.clear()
    
    # Delete all charts
    try:
        charts = spreadsheet.fetch_sheet_metadata().get('sheets', [{}])[0].get('charts', [])
        if charts:
            requests = [{'deleteEmbeddedObject': {'objectId': c['chartId']}} for c in charts]
            spreadsheet.batch_update({'requests': requests})
    except:
        pass
    
    num_dates = len(dates)
    num_habits = len(habits)
    
    # Day numbers for header (1-27 for Jan 5-31)
    day_numbers = list(range(1, num_dates + 1))
    
    print('📝 Creating clean tracker layout...')
    
    # === ROW 1: Header with days ===
    header = ['Habits'] + [str(d) for d in day_numbers] + ['Done %']
    
    # === HABIT ROWS ===
    all_rows = [header]
    
    for habit in habits:
        row = [habit['name'].replace('🏋️ ', '').replace('💧 ', '').replace('🏃 ', '').replace('😴 ', '').replace('🐍 ', '').replace('💪 ', '').replace('💼 ', '').replace('📚 ', '').replace('🧘 ', '').replace('📱 ', '')]  # Remove emoji for cleaner look
        
        completed = 0
        total = 0
        
        for date in dates:
            status = habit['daily_status'].get(date, '')
            if status == '✓':
                row.append('✓')
                completed += 1
                total += 1
            elif status == '✗':
                row.append('')  # Empty for missed
                total += 1
            else:
                row.append('')  # Empty for pending
        
        # Done %
        progress = round((completed / total * 100) if total > 0 else 0)
        row.append(f'{progress}%')
        
        all_rows.append(row)
    
    # === DAILY DONE % ROW (at top, after header) ===
    # Calculate daily completion percentage
    daily_row = ['Daily Done %']
    total_completed_all = 0
    total_entries_all = 0
    
    for i, date in enumerate(dates):
        day_completed = sum(1 for h in habits if h['daily_status'].get(date) == '✓')
        day_total = num_habits
        pct = round((day_completed / day_total * 100) if day_total > 0 else 0)
        daily_row.append(f'{pct}%')
        total_completed_all += day_completed
        total_entries_all += day_total
    
    overall_pct = round((total_completed_all / total_entries_all * 100) if total_entries_all > 0 else 0)
    daily_row.append(f'{overall_pct}%')
    
    # Insert daily row after header
    all_rows.insert(1, daily_row)
    
    # Write data
    sheet.update(values=all_rows, range_name='A1', value_input_option='USER_ENTERED')
    
    num_rows = len(all_rows)
    last_col = num_dates + 2  # Habits + days + Done%
    
    print('🎨 Applying formatting...')
    
    # Header row - Green background
    sheet.format('A1:AZ1', {
        'backgroundColor': {'red': 0.2, 'green': 0.65, 'blue': 0.33},  # Green like image
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    
    # Daily Done % row - Light purple/blue
    sheet.format(f'A2:AZ2', {
        'backgroundColor': {'red': 0.85, 'green': 0.85, 'blue': 0.95},
        'textFormat': {'bold': True},
        'horizontalAlignment': 'CENTER'
    })
    
    # Habit names column - White with bold
    sheet.format(f'A3:A{num_rows}', {
        'textFormat': {'bold': True}
    })
    
    # Center all cells
    sheet.format(f'B3:AZ{num_rows}', {
        'horizontalAlignment': 'CENTER'
    })
    
    # Done % column - Light color
    done_col = chr(ord('A') + num_dates + 1) if num_dates + 1 < 26 else 'AC'
    sheet.format(f'{done_col}1:{done_col}{num_rows}', {
        'backgroundColor': {'red': 0.9, 'green': 0.95, 'blue': 0.9},
        'textFormat': {'bold': True},
        'horizontalAlignment': 'CENTER'
    })
    
    sheet.freeze(rows=2, cols=1)
    
    print('🔽 Adding dropdown and colors...')
    
    requests = [
        # Data validation for checkmarks
        {
            'setDataValidation': {
                'range': {
                    'sheetId': sheet.id,
                    'startRowIndex': 2,
                    'endRowIndex': num_rows,
                    'startColumnIndex': 1,
                    'endColumnIndex': num_dates + 1
                },
                'rule': {
                    'condition': {
                        'type': 'ONE_OF_LIST',
                        'values': [{'userEnteredValue': '✓'}, {'userEnteredValue': ''}]
                    },
                    'showCustomUi': True,
                    'strict': False
                }
            }
        },
        # Green background for checkmarks
        {
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [{'sheetId': sheet.id, 'startRowIndex': 2, 'endRowIndex': num_rows, 'startColumnIndex': 1, 'endColumnIndex': num_dates + 1}],
                    'booleanRule': {
                        'condition': {'type': 'TEXT_EQ', 'values': [{'userEnteredValue': '✓'}]},
                        'format': {'backgroundColor': {'red': 0.2, 'green': 0.65, 'blue': 0.33}}  # Green
                    }
                },
                'index': 0
            }
        },
        # Column widths
        {'updateDimensionProperties': {'range': {'sheetId': sheet.id, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 1}, 'properties': {'pixelSize': 150}, 'fields': 'pixelSize'}},
        {'updateDimensionProperties': {'range': {'sheetId': sheet.id, 'dimension': 'COLUMNS', 'startIndex': 1, 'endIndex': num_dates + 1}, 'properties': {'pixelSize': 35}, 'fields': 'pixelSize'}},
        {'updateDimensionProperties': {'range': {'sheetId': sheet.id, 'dimension': 'COLUMNS', 'startIndex': num_dates + 1, 'endIndex': num_dates + 2}, 'properties': {'pixelSize': 60}, 'fields': 'pixelSize'}},
        {'updateDimensionProperties': {'range': {'sheetId': sheet.id, 'dimension': 'ROWS', 'startIndex': 0, 'endIndex': num_rows}, 'properties': {'pixelSize': 25}, 'fields': 'pixelSize'}},
        
        # Add DOUGHNUT CHART (Weekly Done %)
        {
            'addChart': {
                'chart': {
                    'spec': {
                        'title': 'Weekly Done %',
                        'pieChart': {
                            'legendPosition': 'NO_LEGEND',
                            'domain': {
                                'sourceRange': {
                                    'sources': [{'sheetId': sheet.id, 'startRowIndex': 0, 'endRowIndex': 1, 'startColumnIndex': 0, 'endColumnIndex': 2}]
                                }
                            },
                            'series': {
                                'sourceRange': {
                                    'sources': [{'sheetId': sheet.id, 'startRowIndex': 1, 'endRowIndex': 2, 'startColumnIndex': num_dates + 1, 'endColumnIndex': num_dates + 2}]
                                }
                            },
                            'pieHole': 0.6  # Big hole = doughnut style
                        },
                        'backgroundColorStyle': {'rgbColor': {'red': 1, 'green': 1, 'blue': 1}}
                    },
                    'position': {
                        'overlayPosition': {
                            'anchorCell': {'sheetId': sheet.id, 'rowIndex': num_rows + 2, 'columnIndex': 0},
                            'widthPixels': 300,
                            'heightPixels': 250
                        }
                    }
                }
            }
        }
    ]
    
    spreadsheet.batch_update({'requests': requests})
    
    print()
    print('✅ Done! Clean tracker created!')
    print()
    print('📊 Layout:')
    print('   Row 1: Header (days 1-27)')
    print('   Row 2: Daily Done % for each day')
    print('   Rows 3+: Habits with checkmarks')
    print('   Last column: Done % per habit')
    print('   Below: Doughnut chart')
    print()
    print('🎯 How to use:')
    print('   - Click any cell and select ✓ from dropdown')
    print('   - Green = done')
    print('   - Empty = not done yet')
    print()
    print(f'🔗 https://docs.google.com/spreadsheets/d/{SHEET_ID}')

if __name__ == '__main__':
    setup_clean_tracker()
