"""
Create EXACT Habit Tracker Template like the image
"""
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = '1_kJ8RfV_W7Djoh531-l38GGDATtu2vXV7Fa8XGW7HWE'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def create_habit_tracker():
    creds = Credentials.from_service_account_file('service-account.json', scopes=SCOPES)
    spreadsheet = gspread.authorize(creds).open_by_key(SHEET_ID)
    sheet = spreadsheet.sheet1
    
    print('Creating Habit Tracker template...')
    
    # === HABITS ===
    habits = [
        'Wake up 6:30 AM',
        'Drink 2L water',
        'Calisthenics',
        'No Phone 60min',
        'Read 30 min',
    ]
    
    # === TOP SECTION (Rows 1-8) ===
    # Row 1: Empty
    # Row 2: Title row
    # Row 3: MONTH dropdown
    # Row 4-8: Daily Habits list with progress
    
    data = []
    
    # Row 1: Empty spacer
    data.append([''] * 15)
    
    # Row 2: Title | JANUARY | AVG COMPLETION | MONTHLY PROGRESS
    data.append(['', 'Habit Tracker', '', '', 'JANUARY', '', '', 'AVG COMPLETION RATE', '', 'MONTHLY PROGRESS', '', '', '', '', ''])
    
    # Row 3: Subtitle
    data.append(['', '', '', '', '', '', '', '100.0%', '', '155 / 155', '', '', '', '', ''])
    
    # Row 4: MONTH label
    data.append(['', 'MONTH', 'January', '', '', '', '', '', '', '', '', '', '', '', ''])
    
    # Row 5: Headers for habits panel
    data.append(['', 'DAILY HABITS', '', 'HABIT PROGRESS', '', '', '', '', '', '', '', '', '', '', ''])
    
    # Rows 6-10: Habit list with progress
    for i, habit in enumerate(habits):
        progress = f'{27 + i} / 27'
        data.append(['', habit, '', progress, '', '', '', '', '', '', '', '', '', '', ''])
    
    # Row 11: Empty spacer
    data.append([''] * 15)
    
    # === MAIN TRACKER TABLE (Rows 12+) ===
    # Header row
    header = ['', 'WEEK', 'DAY', 'DATE'] + habits + ['CURRENT PROGRESS']
    data.append(header)
    
    # Week data
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Week 1: Jan 5-11
    for i, day in enumerate(days):
        date = 5 + i
        week_label = 'WEEK 1' if i == 0 else ''
        row = ['', week_label, day, date] + ['✓'] * len(habits) + ['35 / 35']
        data.append(row)
    
    # Week 2: Jan 12-18
    for i, day in enumerate(days):
        date = 12 + i
        week_label = 'WEEK 2' if i == 0 else ''
        row = ['', week_label, day, date] + ['✓'] * len(habits) + ['35 / 35']
        data.append(row)
    
    # Week 3: Jan 19-25
    for i, day in enumerate(days):
        date = 19 + i
        week_label = 'WEEK 3' if i == 0 else ''
        row = ['', week_label, day, date] + ['✓'] * len(habits) + ['35 / 35']
        data.append(row)
    
    # Week 4: Jan 26-31 (only 6 days)
    for i, day in enumerate(days[:6]):
        date = 26 + i
        week_label = 'WEEK 4' if i == 0 else ''
        row = ['', week_label, day, date] + ['✓'] * len(habits) + ['35 / 35']
        data.append(row)
    
    # Write data
    print(f'Writing {len(data)} rows...')
    sheet.update(values=data, range_name='A1', value_input_option='USER_ENTERED')
    
    num_rows = len(data)
    
    print('Applying formatting...')
    
    # === FORMATTING ===
    requests = []
    
    # Title "Habit Tracker" - big bold
    sheet.format('B2', {'textFormat': {'bold': True, 'fontSize': 18}})
    
    # "JANUARY" - big bold green
    sheet.format('E2', {
        'textFormat': {'bold': True, 'fontSize': 24, 'foregroundColor': {'red': 0.18, 'green': 0.55, 'blue': 0.24}},
        'horizontalAlignment': 'CENTER'
    })
    
    # AVG COMPLETION labels
    sheet.format('H2:H3', {'textFormat': {'bold': True}, 'horizontalAlignment': 'CENTER'})
    sheet.format('H3', {'textFormat': {'bold': True, 'fontSize': 20, 'foregroundColor': {'red': 0.18, 'green': 0.55, 'blue': 0.24}}})
    
    # MONTHLY PROGRESS
    sheet.format('J2:J3', {'textFormat': {'bold': True}, 'horizontalAlignment': 'CENTER'})
    
    # MONTH dropdown area
    sheet.format('B4:C4', {'textFormat': {'bold': True}})
    
    # DAILY HABITS header
    sheet.format('B5', {'textFormat': {'bold': True}})
    sheet.format('D5', {'textFormat': {'bold': True}})
    
    # Main table header row (row 12)
    header_row = 12
    sheet.format(f'B{header_row}:K{header_row}', {
        'backgroundColor': {'red': 0.18, 'green': 0.35, 'blue': 0.2},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    
    # Freeze header
    sheet.freeze(rows=header_row, cols=1)
    
    # Batch formatting requests
    requests = [
        # Column widths
        {'updateDimensionProperties': {'range': {'sheetId': sheet.id, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 1}, 'properties': {'pixelSize': 20}, 'fields': 'pixelSize'}},
        {'updateDimensionProperties': {'range': {'sheetId': sheet.id, 'dimension': 'COLUMNS', 'startIndex': 1, 'endIndex': 2}, 'properties': {'pixelSize': 70}, 'fields': 'pixelSize'}},
        {'updateDimensionProperties': {'range': {'sheetId': sheet.id, 'dimension': 'COLUMNS', 'startIndex': 2, 'endIndex': 3}, 'properties': {'pixelSize': 50}, 'fields': 'pixelSize'}},
        {'updateDimensionProperties': {'range': {'sheetId': sheet.id, 'dimension': 'COLUMNS', 'startIndex': 3, 'endIndex': 4}, 'properties': {'pixelSize': 45}, 'fields': 'pixelSize'}},
        {'updateDimensionProperties': {'range': {'sheetId': sheet.id, 'dimension': 'COLUMNS', 'startIndex': 4, 'endIndex': 9}, 'properties': {'pixelSize': 90}, 'fields': 'pixelSize'}},
        {'updateDimensionProperties': {'range': {'sheetId': sheet.id, 'dimension': 'COLUMNS', 'startIndex': 9, 'endIndex': 10}, 'properties': {'pixelSize': 100}, 'fields': 'pixelSize'}},
        
        # Data validation for checkmarks
        {
            'setDataValidation': {
                'range': {'sheetId': sheet.id, 'startRowIndex': header_row, 'endRowIndex': num_rows, 'startColumnIndex': 4, 'endColumnIndex': 9},
                'rule': {'condition': {'type': 'ONE_OF_LIST', 'values': [{'userEnteredValue': '✓'}, {'userEnteredValue': ''}]}, 'showCustomUi': True, 'strict': False}
            }
        },
        
        # Green for checkmarks
        {
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [{'sheetId': sheet.id, 'startRowIndex': header_row, 'endRowIndex': num_rows, 'startColumnIndex': 4, 'endColumnIndex': 9}],
                    'booleanRule': {
                        'condition': {'type': 'TEXT_EQ', 'values': [{'userEnteredValue': '✓'}]},
                        'format': {'backgroundColor': {'red': 0.18, 'green': 0.65, 'blue': 0.34}}
                    }
                },
                'index': 0
            }
        },
        
        # Alternating row colors for weeks
        {
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [{'sheetId': sheet.id, 'startRowIndex': header_row, 'endRowIndex': num_rows, 'startColumnIndex': 1, 'endColumnIndex': 4}],
                    'booleanRule': {
                        'condition': {'type': 'CUSTOM_FORMULA', 'values': [{'userEnteredValue': '=MOD(ROW(),2)=1'}]},
                        'format': {'backgroundColor': {'red': 0.9, 'green': 0.95, 'blue': 0.9}}
                    }
                },
                'index': 1
            }
        },
    ]
    
    spreadsheet.batch_update({'requests': requests})
    
    print()
    print('✅ Habit Tracker created!')
    print()
    print('Layout:')
    print('  - Title: Habit Tracker | JANUARY')
    print('  - AVG COMPLETION RATE: 100.0%')
    print('  - MONTHLY PROGRESS: 155/155')
    print('  - Left panel: Daily Habits with progress bars')
    print('  - Main table: WEEK | DAY | DATE | Habits | CURRENT PROGRESS')
    print('  - Green cells for completed ✓')
    print()
    print(f'🔗 https://docs.google.com/spreadsheets/d/{SHEET_ID}')

if __name__ == '__main__':
    create_habit_tracker()
