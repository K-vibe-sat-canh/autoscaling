@echo off
echo ============================================
echo    AutoScaling NASA Log - Demo Launcher
echo ============================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    pause
    exit /b 1
)

echo.
echo ============================================
echo    Starting Backend API (FastAPI)
echo ============================================
echo.
echo Backend will run at: http://localhost:8000
echo Swagger Docs at: http://localhost:8000/docs
echo.

:: Start Backend in new window
start "Backend API" cmd /k "cd /d %~dp0 && uvicorn app:app --reload --host 0.0.0.0 --port 8000"

:: Wait for backend to start
echo [INFO] Waiting for Backend to start...
timeout /t 3 /nobreak >nul

echo.
echo ============================================
echo    Starting Frontend (Web UI)
echo ============================================
echo.
echo Frontend will open at: http://localhost:3000
echo.

:: Start Frontend server
start "Frontend Server" cmd /k "cd /d %~dp0 && python serve_frontend.py"

:: Wait and open browser
timeout /t 2 /nobreak >nul

echo.
echo ============================================
echo    Opening Browser...
echo ============================================
start http://localhost:3000
start http://localhost:8000/docs

echo.
echo [SUCCESS] Demo is running!
echo.
echo    Frontend: http://localhost:3000
echo    Backend:  http://localhost:8000
echo    API Docs: http://localhost:8000/docs
echo.
echo Press any key to stop all services...
pause >nul

:: Kill processes
taskkill /FI "WINDOWTITLE eq Backend API*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend Server*" /F >nul 2>&1

echo [INFO] Services stopped.
pause
