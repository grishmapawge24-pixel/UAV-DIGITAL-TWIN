@echo off
REM run_backend.bat
REM =================
REM Double-click this file (or run it from PowerShell/cmd) to start the
REM AeroTwin AI backend on Windows.
REM
REM It assumes you have already:
REM   1. Created a virtual environment:   python -m venv venv
REM   2. Installed dependencies:          venv\Scripts\pip install -r requirements.txt
REM   3. Created a .env file from .env.example with your NGAFID_DATA_PATH
REM (see SETUP_GUIDE.md for the full walkthrough)

setlocal

cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo [!] Virtual environment not found at venv\
    echo     Run these commands first, from this folder, in PowerShell:
    echo         python -m venv venv
    echo         venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

if not exist ".env" (
    echo [!] .env not found - copying .env.example to .env
    echo     Edit .env now and set NGAFID_DATA_PATH, then re-run this script.
    copy .env.example .env
    notepad .env
    exit /b 1
)

echo Starting AeroTwin AI backend on http://localhost:8000  (docs at /docs)
echo Press CTRL+C to stop.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

endlocal
