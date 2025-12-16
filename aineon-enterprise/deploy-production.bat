@echo off
REM ============================================================================
REM AINEON Flash Loan Engine - Production Deployment Script (Windows)
REM Enterprise Tier 0.001% | Profit Generation Mode
REM ============================================================================

setlocal enabledelayedexpansion

REM Color codes
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

set "CONTAINER_NAME=aineon-engine-prod"
set "IMAGE_NAME=aineon-flashloan:latest"
set "COMPOSE_FILE=docker-compose.production.yml"
set "ENV_FILE=.env"

REM Create log directory
if not exist logs\deployment mkdir logs\deployment
set "LOG_FILE=logs\deployment\deployment.log"

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║          AINEON FLASH LOAN ENGINE - PRODUCTION            ║
echo ║              Enterprise Tier 0.001% System                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM ============================================================================
REM Pre-Flight Checks
REM ============================================================================

echo [INFO] Performing pre-flight checks...
echo [%time%] Deployment started >> %LOG_FILE%

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker not installed or not in PATH
    echo [%time%] Docker check FAILED >> %LOG_FILE%
    exit /b 1
)
echo [OK] Docker found
echo [%time%] Docker available >> %LOG_FILE%

REM Check Docker Compose
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose not installed or not in PATH
    echo [%time%] Docker Compose check FAILED >> %LOG_FILE%
    exit /b 1
)
echo [OK] Docker Compose found
echo [%time%] Docker Compose available >> %LOG_FILE%

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Python not found (will skip RPC validation)
) else (
    echo [OK] Python found
)

REM Check for .env file
if not exist %ENV_FILE% (
    echo [ERROR] .env file not found
    if exist .env.example (
        echo [INFO] Creating .env from .env.example...
        copy .env.example %ENV_FILE%
        echo [WARNING] EDIT .env WITH YOUR CREDENTIALS BEFORE DEPLOYING
        echo [%time%] .env created from template >> %LOG_FILE%
    ) else (
        echo [ERROR] .env.example not found
        echo [%time%] .env file missing >> %LOG_FILE%
        exit /b 1
    )
)
echo [OK] .env file exists
echo [%time%] .env file validated >> %LOG_FILE%

REM ============================================================================
REM Environment Validation
REM ============================================================================

echo.
echo [INFO] Validating environment configuration...

REM Simple check for required variables
for /f "tokens=2 delims==" %%a in ('find /i "ETH_RPC_URL=" %ENV_FILE%') do set "RPC_URL=%%a"
if "!RPC_URL!"=="" (
    echo [ERROR] ETH_RPC_URL not configured in .env
    echo [%time%] ETH_RPC_URL validation FAILED >> %LOG_FILE%
    exit /b 1
)
echo [OK] ETH_RPC_URL configured
echo [%time%] ETH_RPC_URL validated >> %LOG_FILE%

for /f "tokens=2 delims==" %%a in ('find /i "WALLET_ADDRESS=" %ENV_FILE%') do set "WALLET=%%a"
if "!WALLET!"=="" (
    echo [ERROR] WALLET_ADDRESS not configured in .env
    echo [%time%] WALLET_ADDRESS validation FAILED >> %LOG_FILE%
    exit /b 1
)
echo [OK] WALLET_ADDRESS configured: !WALLET:~0,10!...
echo [%time%] WALLET_ADDRESS validated >> %LOG_FILE%

REM ============================================================================
REM Docker Build
REM ============================================================================

echo.
echo [INFO] Building Docker image...
echo [%time%] Starting Docker build >> %LOG_FILE%

docker build -t %IMAGE_NAME% -f Dockerfile.production . >> %LOG_FILE% 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker build failed
    echo [%time%] Docker build FAILED >> %LOG_FILE%
    exit /b 1
)
echo [OK] Docker image built successfully: %IMAGE_NAME%
echo [%time%] Docker image built >> %LOG_FILE%

REM ============================================================================
REM Docker Deployment
REM ============================================================================

echo.
echo [INFO] Deploying containers...
echo [%time%] Starting deployment >> %LOG_FILE%

REM Stop existing containers
docker-compose -f %COMPOSE_FILE% down >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Stopped existing containers
    timeout /t 2 /nobreak
)

REM Start new containers
docker-compose -f %COMPOSE_FILE% up -d >> %LOG_FILE% 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose failed to start
    echo [%time%] Docker Compose startup FAILED >> %LOG_FILE%
    docker-compose -f %COMPOSE_FILE% logs
    exit /b 1
)
echo [OK] Docker Compose started
echo [%time%] Docker Compose deployed >> %LOG_FILE%

REM ============================================================================
REM Health Checks
REM ============================================================================

echo.
echo [INFO] Waiting for system health (max 90 seconds)...
echo [%time%] Health check started >> %LOG_FILE%

setlocal enabledelayedexpansion
set "ATTEMPTS=0"
set "MAX_ATTEMPTS=30"

:health_check_loop
set /a ATTEMPTS+=1

if %ATTEMPTS% gtr %MAX_ATTEMPTS% (
    echo [ERROR] System failed to become healthy
    echo [%time%] Health check timeout >> %LOG_FILE%
    docker logs %CONTAINER_NAME%
    exit /b 1
)

echo [%ATTEMPTS%/%MAX_ATTEMPTS%] Checking health...

REM Try to call health endpoint
for /f "tokens=*" %%a in ('powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8081/health' -TimeoutSec 2 -ErrorAction Stop | Select-Object -ExpandProperty StatusCode } catch { Write-Output 'Error' }" 2^>nul') do set "HEALTH_STATUS=%%a"

if "!HEALTH_STATUS!"=="200" (
    echo [OK] API Health Check: PASSED
    echo [%time%] Health check passed >> %LOG_FILE%
    goto health_check_success
)

timeout /t 3 /nobreak >nul

goto health_check_loop

:health_check_success

REM ============================================================================
REM System Validation
REM ============================================================================

echo.
echo [INFO] Validating system endpoints...
echo [%time%] Endpoint validation started >> %LOG_FILE%

REM Check status endpoint
echo [INFO] Checking /status endpoint...
for /f "tokens=*" %%a in ('powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8081/status' -TimeoutSec 5 -ErrorAction Stop | Select-Object -ExpandProperty Content } catch { Write-Output 'Error' }" 2^>nul') do set "STATUS_RESPONSE=%%a"

if "!STATUS_RESPONSE!"=="Error" (
    echo [WARNING] Could not fetch status
) else (
    echo [OK] Status endpoint responding
    echo [%time%] Status endpoint validated >> %LOG_FILE%
)

REM Check container status
for /f "tokens=*" %%a in ('docker ps --filter "name=%CONTAINER_NAME%" --format "table {{.Names}}"') do set "CONTAINER_STATUS=%%a"

if "!CONTAINER_STATUS!"=="" (
    echo [ERROR] Container is not running
    echo [%time%] Container not running >> %LOG_FILE%
    exit /b 1
) else (
    echo [OK] Container is running
    echo [%time%] Container validation passed >> %LOG_FILE%
)

REM ============================================================================
REM Deployment Summary
REM ============================================================================

echo.
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║            DEPLOYMENT SUMMARY - SUCCESS                   ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo System Information:
echo   Container Name:     %CONTAINER_NAME%
echo   Image:              %IMAGE_NAME%
echo   Mode:               PRODUCTION (NO MOCK/SIM)
echo   Tier:               ENTERPRISE 0.001%%
echo.

echo Endpoints (LOCALHOST):
echo   API Server:         http://localhost:8081
echo     - Health:         http://localhost:8081/health
echo     - Status:         http://localhost:8081/status
echo     - Profit:         http://localhost:8081/profit
echo     - Opportunities:  http://localhost:8081/opportunities
echo     - Audit:          http://localhost:8081/audit
echo     - Report:         http://localhost:8081/audit/report
echo.
echo   Monitoring:         http://localhost:8082
echo   Dashboard:          http://localhost:8089
echo.

echo Useful Commands:
echo   View logs:          docker logs -f %CONTAINER_NAME%
echo   Check status:       curl http://localhost:8081/status
echo   View profit:        curl http://localhost:8081/profit
echo   Stop container:     docker-compose -f %COMPOSE_FILE% down
echo   Restart container:  docker-compose -f %COMPOSE_FILE% restart
echo.

echo Profit Generation Configuration:
echo   Mode:               ENTERPRISE_TIER_0.001%%
echo   Auto Transfer:      Enabled
echo   Profit Threshold:   5.0 ETH
echo   Min Profit/Trade:   0.5 ETH
echo.

echo Next Steps:
echo   1. Monitor system:   curl http://localhost:8081/status
echo   2. View dashboard:   start http://localhost:8089
echo   3. Check profit:     curl http://localhost:8081/profit
echo   4. View logs:        docker logs -f %CONTAINER_NAME%
echo.

echo [%time%] Deployment completed successfully >> %LOG_FILE%

echo.
pause
