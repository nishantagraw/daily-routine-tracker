"""
Google Sheets Sync Script for Daily Routine Tracker
Run this to sync your local tracker data to Google Sheets

Usage: python sync_to_sheets.py [SPREADSHEET_ID]

If no SPREADSHEET_ID is provided, it will try to create a new sheet
or you can provide an existing sheet ID to sync to.
"""

import gspread
from google.oauth2.service_account import Credentials
import json
import os
import sys

# Configuration
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), 'service-account.json')
DATA_FILE = os.path.join(os.path.dirname(__file__), 'tracker_data.json')
SPREADSHEET_NAME = "Daily Routine Tracker 2026"

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def load_local_data():
    """Load data from local JSON file"""
    if not os.path.exists(DATA_FILE):
        print("❌ No local data found. Run the tracker first!")
        return None
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_sheets_client():
    """Get authenticated Google Sheets client"""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return gspread.authorize(creds)

def open_or_create_sheet(client, sheet_id=None):
    """Open existing sheet or create new one"""
    
    if sheet_id:
        try:
            spreadsheet = client.open_by_key(sheet_id)
            print(f"✅ Opened spreadsheet: {spreadsheet.title}")
            return spreadsheet
        except Exception as e:
            print(f"❌ Could not open spreadsheet with ID: {sheet_id}")
            print(f"   Error: {e}")
            return None
    
    # Try to find existing
    try:
        spreadsheet = client.open(SPREADSHEET_NAME)
        print(f"✅ Found existing spreadsheet: {SPREADSHEET_NAME}")
        return spreadsheet
    except gspread.SpreadsheetNotFound:
        pass
    
    # Create new
    try:
        spreadsheet = client.create(SPREADSHEET_NAME)
        spreadsheet.share('infiniteclub14@gmail.com', perm_type='user', role='writer')
        print(f"✅ Created new spreadsheet: {SPREADSHEET_NAME}")
        print(f"📎 ID: {spreadsheet.id}")
        print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")
        return spreadsheet
    except Exception as e:
        print(f"❌ Could not create spreadsheet: {e}")
        print("\n💡 TIP: Your Google Drive storage might be full.")
        print("   Delete some files or use an existing spreadsheet ID.")
        return None

def sync_to_sheet(spreadsheet, data):
    """Sync local data to Google Sheets"""
    
    sheet = spreadsheet.sheet1
    
    # Clear existing data
    sheet.clear()
    
    # Create headers
    headers = ["Habit"] + data["dates"] + ["Total ✓", "Total ✗", "Progress %", "Streak 🔥"]
    
    # Prepare all data
    all_rows = [headers]
    
    for habit in data["habits"]:
        row = [habit["name"]]
        
        completed = 0
        missed = 0
        streak = 0
        counting_streak = True
        
        for date in data["dates"]:
            status = habit["daily_status"].get(date, "")
            row.append(status)
            
            if status == "✓":
                completed += 1
                if counting_streak:
                    streak += 1
            elif status == "✗":
                missed += 1
                counting_streak = False
        
        total = completed + missed
        progress = round((completed / total * 100) if total > 0 else 0, 1)
        
        row.extend([completed, missed, f"{progress}%", streak])
        all_rows.append(row)
    
    # Update sheet
    sheet.update(f'A1:AK{len(all_rows)}', all_rows)
    
    # Format
    sheet.freeze(rows=1, cols=1)
    
    print(f"✅ Synced {len(data['habits'])} habits to Google Sheets!")

def main():
    print("\n" + "=" * 50)
    print("📊 Daily Routine Tracker - Google Sheets Sync")
    print("=" * 50 + "\n")
    
    # Load local data
    data = load_local_data()
    if not data:
        return
    
    print(f"📁 Found {len(data['habits'])} habits in local data")
    
    # Get sheet ID from command line if provided
    sheet_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Connect to Google Sheets
    try:
        client = get_sheets_client()
        print("✅ Connected to Google Sheets API")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    # Open or create spreadsheet
    spreadsheet = open_or_create_sheet(client, sheet_id)
    if not spreadsheet:
        return
    
    # Sync data
    sync_to_sheet(spreadsheet, data)
    
    print("\n" + "=" * 50)
    print(f"🔗 View your sheet: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")
    print("=" * 50 + "\n")

if __name__ == '__main__':
    main()
