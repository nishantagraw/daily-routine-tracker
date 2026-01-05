@echo off
echo ============================================
echo    Daily Routine Tracker - Starting...
echo ============================================
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt -q

echo.
echo ============================================
echo    Starting Backend Server...
echo ============================================
echo.

start python app.py

REM Wait a bit for server to start
timeout /t 3 /nobreak > nul

echo.
echo ============================================
echo    Opening Dashboard in Browser...
echo ============================================
echo.

start "" "index.html"

echo.
echo Server running at: http://localhost:5200
echo Dashboard opened in your default browser
echo.
echo Press any key to stop the server...
pause > nul
