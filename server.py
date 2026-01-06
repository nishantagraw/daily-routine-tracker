"""
Daily Routine Tracker - Production Server with MongoDB
Serves both API and frontend for Render deployment
"""

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from pymongo import MongoClient
import os
from datetime import datetime

app = Flask(__name__, static_folder='.')
CORS(app)

# MongoDB Connection - Get from environment variable only (no hardcoded password!)
MONGO_URI = os.environ.get('MONGO_URI')

# Connect to MongoDB
try:
    client = MongoClient(MONGO_URI)
    db = client['routine_tracker']
    habits_collection = db['habits']
    settings_collection = db['settings']
    print("✅ Connected to MongoDB!")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    client = None
    db = None

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
    """Load data from MongoDB"""
    if not db:
        return {"dates": get_january_dates(), "habits": DEFAULT_HABITS}
    
    try:
        # Get settings (dates)
        settings = settings_collection.find_one({"type": "dates"})
        dates = settings.get("dates", get_january_dates()) if settings else get_january_dates()
        
        # Get habits
        habits = list(habits_collection.find({}, {"_id": 0}))
        
        if not habits:
            # Initialize with defaults
            for habit in DEFAULT_HABITS:
                habits_collection.insert_one(habit)
            habits = DEFAULT_HABITS.copy()
            
            # Save dates
            settings_collection.update_one(
                {"type": "dates"},
                {"$set": {"dates": dates}},
                upsert=True
            )
        
        return {"dates": dates, "habits": habits}
    except Exception as e:
        print(f"Error loading data: {e}")
        return {"dates": get_january_dates(), "habits": DEFAULT_HABITS}

def save_habit(habit_name, daily_status):
    """Save habit status to MongoDB"""
    if not db:
        return False
    try:
        habits_collection.update_one(
            {"name": habit_name},
            {"$set": {"daily_status": daily_status}}
        )
        return True
    except Exception as e:
        print(f"Error saving habit: {e}")
        return False

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
        
        if db:
            # Get current habit
            habit = habits_collection.find_one({"name": habit_name})
            if habit:
                daily_status = habit.get("daily_status", {})
                daily_status[date] = status
                habits_collection.update_one(
                    {"name": habit_name},
                    {"$set": {"daily_status": daily_status}}
                )
        
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
        
        if db:
            habits_collection.insert_one(new_habit)
        
        return jsonify({"success": True, "message": f"Added: {habit_name}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/habits/delete', methods=['POST'])
def delete_habit():
    try:
        req_data = request.json
        habit_name = req_data.get('habit_name')
        
        if db:
            habits_collection.delete_one({"name": habit_name})
        
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
        
        if db:
            habits_collection.update_one(
                {"name": old_name},
                {"$set": {"name": f"{emoji} {new_name}", "emoji": emoji}}
            )
        
        return jsonify({"success": True, "message": f"Updated habit"})
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
    return jsonify({"connected": db is not None, "message": "MongoDB connected" if db else "No database"})

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    return jsonify({"database": "MongoDB Atlas", "connected": db is not None})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
