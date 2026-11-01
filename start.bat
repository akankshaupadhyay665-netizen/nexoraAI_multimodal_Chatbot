@echo off
TITLE NEXORA AI Launcher
COLOR 0B

echo ======================================================================
echo    _  _ _______ _     _  _____   ______ _______        _______ _____ 
echo    ^|\ ^| ^|______  \___/  ^|     ^| ^|_____/ ^|_____^|       ^|_____^|   ^|   
echo    ^| \^| ^|______ _/   \_ ^|_____^| ^|    \_ ^|     ^| _____ ^|     ^| __^|__ 
echo                                                                      
echo            One Intelligence. Infinite Possibilities.
echo ======================================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from python.org
    pause
    exit /b 1
)

echo [1/3] Starting NEXORA AI FastAPI Backend on http://127.0.0.1:8000 ...
start "Nexora Backend (Port 8000)" cmd /k "python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [2/3] Starting NEXORA AI Frontend Server on http://127.0.0.1:5500 ...
start "Nexora Frontend (Port 5500)" cmd /k "python serve_frontend.py"

timeout /t 2 /nobreak >nul

echo [3/3] Opening Nexora AI in your default web browser...
start http://127.0.0.1:5500

echo.
echo ======================================================================
echo   NEXORA AI is running locally!
echo   - Frontend:          http://127.0.0.1:5500
echo   - Backend:           http://127.0.0.1:8000
echo   - API Documentation: http://127.0.0.1:8000/docs
echo ======================================================================
echo.
echo Press any key to close this launcher window (servers will continue running)...
pause >nul






