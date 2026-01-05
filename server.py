"""
Daily Routine Tracker - Production Server
Serves both API and frontend for Render deployment
"""

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='.')
CORS(app)

# Data file path
DATA_FILE = os.path.join(os.path.dirname(__file__), 'tracker_data.json')

# Default habits
DEFAULT_HABITS = [
    {"name": "🏋️ Calisthenics", "emoji": "🏋️", "daily_status": {}},
    {"name": "💧 Water (8 glasses)", "emoji": "💧", "daily_status": {}},
    {"name": "🏃 Running", "emoji": "🏃", "daily_status": {}},
    {"name": "😴 Sleep (7+ hours)", "emoji": "😴", "daily_status": {}},
    {"name": "🐍 Learning Python", "emoji": "🐍", "daily_status": {}},
    {"name": "💪 Protein Intake", "emoji": "💪", "daily_status": {}},
    {"name": "💼 Client Finding (1hr)", "emoji": "💼", "daily_status": {}},
    {"name": "📚 Reading (30 min)", "emoji": "📚", "daily_status": {}},
    {"name": "🧘 Meditation (10 min)", "emoji": "🧘", "daily_status": {}},
    {"name": "📱 No Social Media (1st hr)", "emoji": "📱", "daily_status": {}},
    {"name": "💪 Morning Walk", "emoji": "💪", "daily_status": {}},
]

def get_january_dates():
    """Get dates from Jan 5 to Jan 31"""
    return [f"{i:02d} Jan" for i in range(5, 32)]

def load_data():
    """Load data from file or create default"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('habits') and data.get('dates'):
                    return data
    except:
        pass
    
    # Create default data
    return {
        "dates": get_january_dates(),
        "habits": DEFAULT_HABITS
    }

def save_data(data):
    """Save data to file"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ===================================
# Static File Routes (Frontend)
# ===================================

@app.route('/')
def serve_index():
    return send_file('index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

# ===================================
# API Routes
# ===================================

@app.route('/api/habits', methods=['GET'])
def get_habits():
    data = load_data()
    return jsonify({
        "habits": data["habits"],
        "dates": data["dates"],
        "spreadsheet_url": ""
    })

@app.route('/api/habits/status', methods=['POST'])
def update_status():
    try:
        req_data = request.json
        habit_name = req_data.get('habit_name')
        date = req_data.get('date')
        status = req_data.get('status')
        
        data = load_data()
        
        for habit in data["habits"]:
            if habit["name"] == habit_name:
                habit["daily_status"][date] = status
                break
        
        save_data(data)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/habits/add', methods=['POST'])
def add_habit():
    try:
        req_data = request.json
        habit_name = req_data.get('name')
        emoji = req_data.get('emoji', '📌')
        
        data = load_data()
        
        new_habit = {
            "name": f"{emoji} {habit_name}",
            "emoji": emoji,
            "daily_status": {}
        }
        
        data["habits"].append(new_habit)
        save_data(data)
        
        return jsonify({"success": True, "message": f"Added: {habit_name}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/habits/delete', methods=['POST'])
def delete_habit():
    try:
        req_data = request.json
        habit_name = req_data.get('habit_name')
        
        data = load_data()
        data["habits"] = [h for h in data["habits"] if h["name"] != habit_name]
        save_data(data)
        
        return jsonify({"success": True, "message": f"Deleted: {habit_name}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        data = load_data()
        
        total_completed = 0
        total_missed = 0
        best_streak = 0
        
        for habit in data["habits"]:
            streak = 0
            for date in data["dates"]:
                status = habit["daily_status"].get(date, "")
                if status == "✓":
                    total_completed += 1
                    streak += 1
                    best_streak = max(best_streak, streak)
                elif status == "✗":
                    total_missed += 1
                    streak = 0
        
        total = total_completed + total_missed
        progress = round((total_completed / total * 100) if total > 0 else 0)
        
        return jsonify({
            "overall_progress": progress,
            "total_completed": total_completed,
            "total_missed": total_missed,
            "best_streak": best_streak,
            "total_habits": len(data["habits"]),
            "total_days": len(data["dates"])
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/week/<int:week_num>', methods=['GET'])
def get_week(week_num):
    try:
        data = load_data()
        dates = data["dates"]
        
        # Calculate week dates (7 days per week)
        start_idx = (week_num - 1) * 7
        end_idx = min(start_idx + 7, len(dates))
        week_dates = dates[start_idx:end_idx]
        
        return jsonify({
            "week": week_num,
            "dates": week_dates,
            "habits": data["habits"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sheets/status', methods=['GET'])
def sheets_status():
    return jsonify({"connected": False, "message": "Cloud version - no Google Sheets sync"})

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    return jsonify({"spreadsheet_id": "", "message": "Cloud version"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
