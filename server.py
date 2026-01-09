"""
Daily Routine Tracker - Simple Production Server
Works without MongoDB - uses in-memory storage
"""

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import os
import json

app = Flask(__name__, static_folder='.')
CORS(app)

# In-memory data storage (resets when server restarts)
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
    return [f"{i:02d} Jan" for i in range(10, 32)]  # Start from Jan 10

# In-memory data
app_data = {
    "dates": get_january_dates(),
    "habits": DEFAULT_HABITS.copy()
}

def load_data():
    """Load data from file or use defaults"""
    global app_data
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('habits') and data.get('dates'):
                    app_data = data
                    return data
    except Exception as e:
        print(f"Error loading data: {e}")
    return app_data

def save_data():
    """Save data to file"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(app_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving data: {e}")

# Load data on startup
load_data()

# ===================================
# Static File Routes (Frontend)
# ===================================

@app.route('/')
def serve_index():
    return send_file('index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    if filename.startswith('api/'):
        return jsonify({"error": "Not found"}), 404
    return send_from_directory('.', filename)

# ===================================
# API Routes
# ===================================

@app.route('/api/init', methods=['POST', 'GET'])
def init_app():
    """Initialize the app - required by frontend"""
    return jsonify({
        "success": True,
        "spreadsheet_url": "",
        "message": "App initialized"
    })

@app.route('/api/habits', methods=['GET'])
def get_habits():
    return jsonify({
        "habits": app_data["habits"],
        "dates": app_data["dates"],
        "spreadsheet_url": ""
    })

@app.route('/api/habits/status', methods=['POST'])
def update_status():
    try:
        req_data = request.json
        habit_name = req_data.get('habit_name')
        date = req_data.get('date')
        status = req_data.get('status')
        
        for habit in app_data["habits"]:
            if habit["name"] == habit_name:
                habit["daily_status"][date] = status
                break
        
        save_data()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/habits/add', methods=['POST'])
def add_habit():
    try:
        req_data = request.json
        habit_name = req_data.get('name')
        emoji = req_data.get('emoji', '📌')
        
        new_habit = {
            "name": f"{emoji} {habit_name}",
            "emoji": emoji,
            "daily_status": {}
        }
        
        app_data["habits"].append(new_habit)
        save_data()
        
        return jsonify({"success": True, "message": f"Added: {habit_name}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/habits/delete', methods=['POST'])
def delete_habit():
    try:
        req_data = request.json
        habit_name = req_data.get('habit_name')
        
        app_data["habits"] = [h for h in app_data["habits"] if h["name"] != habit_name]
        save_data()
        
        return jsonify({"success": True, "message": f"Deleted: {habit_name}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/habits/edit', methods=['POST'])
def edit_habit():
    try:
        req_data = request.json
        old_name = req_data.get('old_name')
        new_name = req_data.get('new_name')
        emoji = req_data.get('emoji', '📌')
        
        for habit in app_data["habits"]:
            if habit["name"] == old_name:
                habit["name"] = f"{emoji} {new_name}"
                habit["emoji"] = emoji
                break
        
        save_data()
        return jsonify({"success": True, "message": f"Updated habit"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        total_completed = 0
        total_missed = 0
        best_streak = 0
        
        for habit in app_data["habits"]:
            streak = 0
            for date in app_data["dates"]:
                status = habit.get("daily_status", {}).get(date, "")
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
            "total_habits": len(app_data["habits"]),
            "total_days": len(app_data["dates"])
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/week/<int:week_num>', methods=['GET'])
def get_week(week_num):
    try:
        dates = app_data["dates"]
        
        start_idx = (week_num - 1) * 7
        end_idx = min(start_idx + 7, len(dates))
        week_dates = dates[start_idx:end_idx]
        
        return jsonify({
            "week": week_num,
            "dates": week_dates,
            "habits": app_data["habits"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sheets/status', methods=['GET'])
def sheets_status():
    return jsonify({"connected": True, "message": "File-based storage"})

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    return jsonify({"storage": "file", "connected": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
