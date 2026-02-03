@echo off
echo ========================================================
echo   AutoScaling Analysis Project - One-Click Launcher
echo ========================================================
echo.

echo [1/3] Activating Python Environment...
call .venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Error: Virtual environment not found! Please create it first.
    pause
    exit /b
)

echo [2/3] Starting Backend API (Port 8000)...
start "Backend API" cmd /k "uvicorn app:app --reload"

echo [3/3] Starting Dashboard UI (Port 8501)...
start "Streamlit Dashboard" cmd /k "streamlit run dashboard/main.py"

echo.
echo ========================================================
echo   System is running!
echo   - API Docs:  http://localhost:8000/docs
echo   - Dashboard: http://localhost:8501
echo ========================================================
echo   Press any key to close this launcher...
pause
