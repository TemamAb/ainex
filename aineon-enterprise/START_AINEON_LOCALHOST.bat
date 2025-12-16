@echo off
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║           AINEON ENTERPRISE ENGINE - LOCALHOST               ║
echo ║                  🚀 PROFIT GENERATION MODE 🚀                ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo [*] Starting AINEON Engine on localhost:8081
echo [*] Profit Mode: AUTOMATIC
echo [*] Transfer Mode: ENABLED
echo.

REM Set environment
set PORT=8081
set PYTHONUNBUFFERED=1

REM Start the engine
python core/main.py

pause
