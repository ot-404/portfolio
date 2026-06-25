@echo off
REM Double-click this file (or run it in a terminal) to start the portfolio.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment and installing dependencies...
    python -m venv .venv
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

echo.
echo Starting portfolio at http://127.0.0.1:5000
echo Press Ctrl+C to stop.
echo.
".venv\Scripts\python.exe" app.py
pause
