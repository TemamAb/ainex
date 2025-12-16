@echo off
REM ============================================================================
REM AINEON Terminal Profit Monitor - Windows Batch Script
REM Real-time profit metrics display with manual withdrawal mode
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║     AINEON TERMINAL PROFIT MONITOR - MANUAL WITHDRAWAL MODE        ║
echo ║                   Real-time Profit Display                         ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

REM Check if .env exists
if not exist .env (
    echo [ERROR] .env file not found
    echo [INFO] Please copy .env.example to .env and configure it first
    pause
    exit /b 1
)

REM Load environment variables
for /f "tokens=*" %%a in ('type .env ^| findstr /v "^REM" ^| findstr /v "^#"') do (
    set "%%a"
)

REM Verify RPC is configured
if "!ETH_RPC_URL!"=="" (
    echo [ERROR] ETH_RPC_URL not configured in .env
    pause
    exit /b 1
)

echo [INFO] Environment loaded
echo [INFO] RPC: !ETH_RPC_URL:~0,40!...
echo [INFO] Wallet: !WALLET_ADDRESS:~0,10!...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH
    echo [INFO] Please install Python 3.9 or higher
    pause
    exit /b 1
)

echo [INFO] Starting terminal profit monitor...
echo [INFO] Press Ctrl+C to stop
echo.
timeout /t 2 /nobreak >nul

REM Run the monitor
python terminal_profit_monitor.py

if %errorlevel% equ 0 (
    echo [SUCCESS] Monitor stopped cleanly
) else (
    echo [ERROR] Monitor encountered an error
)

pause
