# Daily Routine Tracker 🎯

A beautiful, aesthetic daily routine tracker with Google Sheets integration.

## Features

- ✅ **Tick/Cross Toggle** - Click to mark habits as completed or missed
- 📊 **Charts & Visualizations** - See your progress with beautiful charts
- 🔥 **Streak Counter** - Track consecutive days of habit completion
- 📈 **Progress Tracking** - Individual and overall progress percentages
- 🌙 **Dark/Light Mode** - Toggle between themes
- 🗓️ **Weekly/Monthly Views** - Switch between view modes
- 📱 **Google Sheets Sync** - Two-way sync with Google Sheets
- ➕ **Add Custom Habits** - Add your own habits to track

## Habits Tracked (Default)

1. 🏋️ Calisthenics
2. 💧 Water (8 glasses)
3. 🏃 Running
4. 😴 Sleep (7+ hours)
5. 🐍 Learning Python
6. 🥩 Protein Intake
7. 💼 Client Finding (1hr)
8. 📚 Reading (30 min)
9. 🧘 Meditation (10 min)
10. 📱 No Social Media (1st hr)

## Quick Start

### Option 1: Double-click start.bat
Just double-click `start.bat` and it will:
1. Install dependencies
2. Start the backend server
3. Open the dashboard in your browser

### Option 2: Manual Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the backend server:
```bash
python app.py
```

3. Open `index.html` in your browser

## How It Works

1. **Backend (Flask)** - Connects to Google Sheets API
2. **Frontend (HTML/CSS/JS)** - Beautiful dashboard with Chart.js
3. **Google Sheets** - Persistent storage, edit from anywhere

## Google Sheets

After first run, a new Google Sheet will be created:
- **Name**: "Daily Routine Tracker 2026"
- **Shared with**: infiniteclub14@gmail.com

You can edit directly in Google Sheets AND the web dashboard - they sync!

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/init` | POST | Initialize spreadsheet |
| `/api/habits` | GET | Get all habits data |
| `/api/habits/update` | POST | Update habit status |
| `/api/habits/add` | POST | Add new habit |
| `/api/stats` | GET | Get overall statistics |
| `/api/week/<num>` | GET | Get week-specific data |

## Files

```
daily-routine-tracker/
├── app.py              # Flask backend
├── index.html          # Dashboard UI
├── style.css           # Styles (dark/light mode)
├── script.js           # Frontend logic
├── requirements.txt    # Python dependencies
├── service-account.json # Google API credentials
├── start.bat           # Easy launcher
└── README.md           # This file
```

## Customize

- Add new habits via the "Add Habit" button
- Change themes using the theme toggle (☀️/🌙)
- Edit habits directly in the Google Sheet

---

Made with 💜 for Nishu | © 2026 Infinite Club
