@echo off
REM ============================================================================
REM AINEON Complete Setup - Windows
REM Reads .env, configures manual withdrawal, and starts monitoring
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║          AINEON COMPLETE SETUP - MANUAL WITHDRAWAL MODE           ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

REM Step 1: Check for .env file
if not exist .env (
    echo [ERROR] .env file not found
    echo [INFO] Please create .env file with your configuration first
    pause
    exit /b 1
)

echo [STEP 1] Validating .env file...
python setup_manual_withdrawal.py

if %errorlevel% neq 0 (
    echo [ERROR] Setup configuration failed
    pause
    exit /b 1
)

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║         SETUP COMPLETE - READY TO DEPLOY AND MONITOR              ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

echo [NEXT STEPS]
echo.
echo 1. Deploy AINEON Engine:
echo    deploy-production.bat
echo.
echo 2. Start Terminal Profit Monitor (in another terminal):
echo    run-terminal-monitor.bat
echo.
echo 3. Watch real-time profit metrics accumulate
echo.
echo 4. When profit reaches 5.0 ETH, withdraw manually:
echo    curl -X POST http://localhost:8081/withdraw
echo.

pause
