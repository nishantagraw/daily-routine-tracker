@echo off
title Daily Routine Tracker
cd /d "c:\Users\megha\infinite club\daily-routine-tracker"

echo.
echo ============================================================
echo    🎯 DAILY ROUTINE TRACKER - Starting...
echo ============================================================
echo.

:: Kill any existing processes on ports 5200 and 5201
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5200 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5201 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1

echo Starting backend server...
start /B python app.py

:: Wait for server to start
timeout /t 3 /nobreak >nul

echo Starting web server...
start /B python -m http.server 5201

:: Wait a bit more
timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo    ✅ Routine Tracker is RUNNING!
echo ============================================================
echo.
echo    📊 Dashboard: http://localhost:5201
echo    📱 Mobile:    http://%COMPUTERNAME%:5201
echo.
echo    Press Ctrl+C or close this window to stop.
echo ============================================================
echo.

:: Open in browser
start "" "http://localhost:5201"

:: Keep window open
cmd /k
