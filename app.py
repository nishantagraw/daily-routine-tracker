"""
Daily Routine Tracker - Backend API
With Google Sheets two-way sync + local backup
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import json
import os
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)
CORS(app)

# Configuration
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), 'service-account.json')
DATA_FILE = os.path.join(os.path.dirname(__file__), 'tracker_data.json')
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

# Google Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Global variables
sheets_client = None
spreadsheet = None
sheet = None
SHEET_ID = None
USE_SHEETS = False

# Default habits configuration
DEFAULT_HABITS = [
    {"id": "calisthenics", "name": "🏋️ Calisthenics", "emoji": "🏋️", "category": "fitness"},
    {"id": "water", "name": "💧 Water (8 glasses)", "emoji": "💧", "category": "health"},
    {"id": "running", "name": "🏃 Running", "emoji": "🏃", "category": "fitness"},
    {"id": "sleep", "name": "😴 Sleep (7+ hours)", "emoji": "😴", "category": "health"},
    {"id": "python", "name": "🐍 Learning Python", "emoji": "🐍", "category": "learning"},
    {"id": "protein", "name": "🥩 Protein Intake", "emoji": "🥩", "category": "health"},
    {"id": "client_finding", "name": "💼 Client Finding (1hr)", "emoji": "💼", "category": "business"},
    {"id": "reading", "name": "📚 Reading (30 min)", "emoji": "📚", "category": "learning"},
    {"id": "meditation", "name": "🧘 Meditation (10 min)", "emoji": "🧘", "category": "mindfulness"},
    {"id": "no_social_media", "name": "📱 No Social Media (1st hr)", "emoji": "📱", "category": "productivity"},
]

# Generate dates for January 2026 (starting from Jan 5)
def get_january_dates():
    dates = []
    start_date = datetime(2026, 1, 5)
    end_date = datetime(2026, 1, 31)
    current = start_date
    while current <= end_date:
        dates.append(current.strftime("%d %b"))
        current += timedelta(days=1)
    return dates

JANUARY_DATES = get_january_dates()

# ===================================
# Configuration Management
# ===================================

def load_config():
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"spreadsheet_id": None}

def save_config(config):
    """Save configuration to file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

# ===================================
# Google Sheets Functions
# ===================================

def init_sheets():
    """Initialize Google Sheets connection"""
    global sheets_client, spreadsheet, sheet, SHEET_ID, USE_SHEETS
    
    config = load_config()
    SHEET_ID = config.get("spreadsheet_id")
    
    if not SHEET_ID:
        print("⚠️ No Google Sheet configured. Using local storage only.")
        print("💡 To enable Google Sheets sync:")
        print("   1. Create a new Google Sheet at https://sheets.google.com")
        print("   2. Share it with: lead-agent@infinite-club-project.iam.gserviceaccount.com")
        print("   3. Copy the Sheet ID from the URL")
        print("   4. Call POST /api/config with {\"spreadsheet_id\": \"YOUR_SHEET_ID\"}")
        USE_SHEETS = False
        return False
    
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        sheets_client = gspread.authorize(creds)
        spreadsheet = sheets_client.open_by_key(SHEET_ID)
        sheet = spreadsheet.sheet1
        USE_SHEETS = True
        print(f"✅ Connected to Google Sheet: {spreadsheet.title}")
        print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
        return True
    except Exception as e:
        print(f"⚠️ Could not connect to Google Sheets: {e}")
        USE_SHEETS = False
        return False

def sync_to_sheets(data):
    """Sync local data TO Google Sheets"""
    global sheet
    
    if not USE_SHEETS or not sheet:
        return False
    
    try:
        # Clear and rebuild sheet
        sheet.clear()
        
        # Create headers
        headers = ["Habit"] + data["dates"] + ["Total ✓", "Total ✗", "Progress %", "Streak 🔥"]
        
        # Prepare all rows
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
        sheet.freeze(rows=1, cols=1)
        
        print("📤 Synced to Google Sheets")
        return True
    except Exception as e:
        print(f"❌ Sync to sheets failed: {e}")
        return False

def sync_from_sheets():
    """Sync data FROM Google Sheets to local"""
    global sheet
    
    if not USE_SHEETS or not sheet:
        return None
    
    try:
        all_data = sheet.get_all_values()
        
        if not all_data or len(all_data) < 2:
            return None
        
        headers = all_data[0]
        
        # Find date columns (between Habit and summary columns)
        date_columns = headers[1:-4] if len(headers) > 5 else headers[1:]
        
        data = {
            "habits": [],
            "dates": date_columns
        }
        
        for row in all_data[1:]:
            if not row[0]:
                continue
            
            habit = {
                "name": row[0],
                "emoji": row[0][0] if row[0] else "📌",
                "category": "custom",
                "daily_status": {}
            }
            
            for i, date in enumerate(date_columns):
                if i + 1 < len(row):
                    habit["daily_status"][date] = row[i + 1]
                else:
                    habit["daily_status"][date] = ""
            
            data["habits"].append(habit)
        
        print("📥 Synced from Google Sheets")
        return data
    except Exception as e:
        print(f"❌ Sync from sheets failed: {e}")
        return None

# ===================================
# Local Storage Functions
# ===================================

def load_data():
    """Load data from local JSON file"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        data = initialize_default_data()
        save_data(data)
        return data

def save_data(data):
    """Save data to local JSON file"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def initialize_default_data():
    """Create default data structure"""
    data = {
        "habits": [],
        "dates": JANUARY_DATES
    }
    
    for habit in DEFAULT_HABITS:
        habit_data = {
            "name": habit["name"],
            "emoji": habit["emoji"],
            "category": habit["category"],
            "daily_status": {}
        }
        for date in JANUARY_DATES:
            habit_data["daily_status"][date] = ""
        data["habits"].append(habit_data)
    
    return data

# ===================================
# Helper Functions
# ===================================

def calculate_streak(daily_status, dates):
    """Calculate current streak from most recent date backwards"""
    streak = 0
    for date in reversed(dates):
        status = daily_status.get(date, "")
        if status == "✓":
            streak += 1
        elif status == "✗":
            break
    return streak

def calculate_habit_stats(habit, dates):
    """Calculate stats for a single habit"""
    completed = 0
    missed = 0
    
    for date in dates:
        status = habit["daily_status"].get(date, "")
        if status == "✓":
            completed += 1
        elif status == "✗":
            missed += 1
    
    total = completed + missed
    progress = round((completed / total * 100) if total > 0 else 0, 1)
    streak = calculate_streak(habit["daily_status"], dates)
    
    return {
        "completed": completed,
        "missed": missed,
        "progress": progress,
        "streak": streak
    }

# ===================================
# API Routes
# ===================================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "sheets_connected": USE_SHEETS,
        "sheet_id": SHEET_ID
    })

@app.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    """Get or set configuration (like spreadsheet ID)"""
    global SHEET_ID, USE_SHEETS
    
    if request.method == 'GET':
        config = load_config()
        config["sheets_connected"] = USE_SHEETS
        return jsonify(config)
    
    elif request.method == 'POST':
        data = request.json
        new_sheet_id = data.get('spreadsheet_id')
        
        if new_sheet_id:
            config = load_config()
            config["spreadsheet_id"] = new_sheet_id
            save_config(config)
            
            # Try to connect
            if init_sheets():
                # Sync local data to new sheet
                local_data = load_data()
                sync_to_sheets(local_data)
                
                return jsonify({
                    "success": True,
                    "message": "Google Sheet connected and synced!",
                    "spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{new_sheet_id}"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Could not connect to the sheet. Make sure it's shared with the service account."
                }), 400
        
        return jsonify({"error": "spreadsheet_id is required"}), 400

@app.route('/api/init', methods=['POST'])
def initialize():
    """Initialize the data"""
    try:
        # Try to sync from sheets first
        if USE_SHEETS:
            sheets_data = sync_from_sheets()
            if sheets_data:
                save_data(sheets_data)
                return jsonify({
                    "success": True,
                    "message": "Synced from Google Sheets!",
                    "sheets_connected": True,
                    "spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
                })
        
        # Fall back to local data
        data = load_data()
        return jsonify({
            "success": True,
            "message": "Loaded from local storage",
            "sheets_connected": USE_SHEETS,
            "spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}" if SHEET_ID else None
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/habits', methods=['GET'])
def get_habits():
    """Get all habits and their data"""
    try:
        # Sync from sheets if connected (to get latest changes)
        if USE_SHEETS:
            sheets_data = sync_from_sheets()
            if sheets_data:
                save_data(sheets_data)
        
        data = load_data()
        
        habits_response = []
        for habit in data["habits"]:
            stats = calculate_habit_stats(habit, data["dates"])
            habits_response.append({
                "name": habit["name"],
                "daily_status": habit["daily_status"],
                "completed": stats["completed"],
                "missed": stats["missed"],
                "progress": stats["progress"],
                "streak": stats["streak"]
            })
        
        return jsonify({
            "habits": habits_response,
            "dates": data["dates"],
            "sheets_connected": USE_SHEETS,
            "spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{SHEET_ID}" if SHEET_ID else None
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/habits/update', methods=['POST'])
def update_habit():
    """Update a habit status for a specific date"""
    try:
        req_data = request.json
        habit_name = req_data.get('habit_name')
        date = req_data.get('date')
        status = req_data.get('status')
        
        if not habit_name or not date:
            return jsonify({"error": "habit_name and date are required"}), 400
        
        data = load_data()
        
        # Find and update the habit
        updated = False
        for habit in data["habits"]:
            if habit["name"] == habit_name:
                habit["daily_status"][date] = status
                updated = True
                break
        
        if not updated:
            return jsonify({"error": f"Habit '{habit_name}' not found"}), 404
        
        # Save locally
        save_data(data)
        
        # Sync to sheets if connected
        if USE_SHEETS:
            sync_to_sheets(data)
        
        return jsonify({
            "success": True,
            "message": f"Updated {habit_name} for {date}",
            "synced_to_sheets": USE_SHEETS
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/habits/add', methods=['POST'])
def add_habit():
    """Add a new habit to track"""
    try:
        req_data = request.json
        habit_name = req_data.get('name')
        emoji = req_data.get('emoji', '📌')
        
        if not habit_name:
            return jsonify({"error": "Habit name is required"}), 400
        
        data = load_data()
        
        # Create new habit
        new_habit = {
            "name": f"{emoji} {habit_name}",
            "emoji": emoji,
            "category": "custom",
            "daily_status": {}
        }
        
        for date in data["dates"]:
            new_habit["daily_status"][date] = ""
        
        data["habits"].append(new_habit)
        save_data(data)
        
        # Sync to sheets
        if USE_SHEETS:
            sync_to_sheets(data)
        
        return jsonify({
            "success": True,
            "message": f"Added new habit: {habit_name}"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/habits/delete', methods=['POST'])
def delete_habit():
    """Delete a habit from the tracker"""
    try:
        req_data = request.json
        habit_name = req_data.get('habit_name')
        
        if not habit_name:
            return jsonify({"error": "Habit name is required"}), 400
        
        data = load_data()
        
        # Find and remove the habit
        original_count = len(data["habits"])
        data["habits"] = [h for h in data["habits"] if h["name"] != habit_name]
        
        if len(data["habits"]) == original_count:
            return jsonify({"error": f"Habit '{habit_name}' not found"}), 404
        
        # Save locally
        save_data(data)
        
        # Sync to sheets
        if USE_SHEETS:
            sync_to_sheets(data)
        
        return jsonify({
            "success": True,
            "message": f"Deleted habit: {habit_name}"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/habits/edit', methods=['POST'])
def edit_habit():
    """Edit/rename a habit"""
    try:
        req_data = request.json
        old_name = req_data.get('old_name')
        new_name = req_data.get('new_name')
        emoji = req_data.get('emoji', '📌')
        
        if not old_name or not new_name:
            return jsonify({"error": "old_name and new_name are required"}), 400
        
        data = load_data()
        
        # Find and update the habit
        updated = False
        for habit in data["habits"]:
            if habit["name"] == old_name:
                habit["name"] = f"{emoji} {new_name}"
                habit["emoji"] = emoji
                updated = True
                break
        
        if not updated:
            return jsonify({"error": f"Habit '{old_name}' not found"}), 404
        
        # Save locally
        save_data(data)
        
        # Sync to sheets
        if USE_SHEETS:
            sync_to_sheets(data)
        
        return jsonify({
            "success": True,
            "message": f"Updated habit to: {emoji} {new_name}"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    try:
        data = load_data()
        
        if not data["habits"]:
            return jsonify({
                "total_habits": 0,
                "overall_progress": 0,
                "best_streak": 0,
                "total_completed": 0,
                "total_missed": 0
            })
        
        total_completed = 0
        total_missed = 0
        best_streak = 0
        
        for habit in data["habits"]:
            stats = calculate_habit_stats(habit, data["dates"])
            total_completed += stats["completed"]
            total_missed += stats["missed"]
            if stats["streak"] > best_streak:
                best_streak = stats["streak"]
        
        total_entries = total_completed + total_missed
        overall_progress = round((total_completed / total_entries * 100) if total_entries > 0 else 0, 1)
        
        return jsonify({
            "total_habits": len(data["habits"]),
            "overall_progress": overall_progress,
            "best_streak": best_streak,
            "total_completed": total_completed,
            "total_missed": total_missed,
            "sheets_connected": USE_SHEETS
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/week/<int:week_num>', methods=['GET'])
def get_week_data(week_num):
    """Get data for a specific week"""
    try:
        data = load_data()
        all_dates = data["dates"]
        
        start_idx = (week_num - 1) * 7
        end_idx = min(start_idx + 7, len(all_dates))
        week_dates = all_dates[start_idx:end_idx]
        
        week_data = []
        for habit in data["habits"]:
            habit_week_status = {}
            completed = 0
            missed = 0
            
            for date in week_dates:
                status = habit["daily_status"].get(date, "")
                habit_week_status[date] = status
                if status == "✓":
                    completed += 1
                elif status == "✗":
                    missed += 1
            
            total = completed + missed
            progress = round((completed / total * 100) if total > 0 else 0, 1)
            streak = calculate_streak(habit["daily_status"], week_dates)
            
            week_data.append({
                "name": habit["name"],
                "daily_status": habit_week_status,
                "completed": completed,
                "missed": missed,
                "progress": progress,
                "streak": streak
            })
        
        return jsonify({
            "week": week_num,
            "dates": week_dates,
            "habits": week_data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sync', methods=['POST'])
def manual_sync():
    """Manually trigger sync with Google Sheets"""
    direction = request.json.get('direction', 'both') if request.json else 'both'
    
    if not USE_SHEETS:
        return jsonify({
            "success": False,
            "error": "Google Sheets not connected"
        }), 400
    
    try:
        if direction in ['from_sheets', 'both']:
            sheets_data = sync_from_sheets()
            if sheets_data:
                save_data(sheets_data)
        
        if direction in ['to_sheets', 'both']:
            data = load_data()
            sync_to_sheets(data)
        
        return jsonify({
            "success": True,
            "message": f"Sync completed ({direction})"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===================================
# Background Sync Thread
# ===================================

def background_sync():
    """Periodically sync with Google Sheets"""
    while True:
        time.sleep(60)  # Sync every 60 seconds
        if USE_SHEETS:
            try:
                sheets_data = sync_from_sheets()
                if sheets_data:
                    save_data(sheets_data)
            except Exception as e:
                print(f"Background sync error: {e}")

# ===================================
# Main
# ===================================

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 DAILY ROUTINE TRACKER")
    print("=" * 60)
    
    # Load local data
    data = load_data()
    print(f"📁 Loaded {len(data['habits'])} habits from local storage")
    
    # Try to connect to Google Sheets
    init_sheets()
    
    # Start background sync thread
    if USE_SHEETS:
        sync_thread = threading.Thread(target=background_sync, daemon=True)
        sync_thread.start()
        print("🔄 Background sync started (every 60 seconds)")
    
    print("=" * 60)
    print("🌐 Dashboard: http://localhost:5200")
    print("📱 Mobile:    http://<YOUR-IP>:5200")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5200, debug=False, threaded=True)
