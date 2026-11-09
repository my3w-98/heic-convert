@echo off
setlocal
cd /d "%~dp0"
title HEIC Convert

where python >nul 2>&1
if errorlevel 1 (
  echo Python was not found on PATH. Install Python 3.11+ and try again.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

REM Use a renamed pythonw copy so the taskbar / process shows "HEIC Convert"
if not exist ".venv\Scripts\HEIC Convert.exe" (
  copy /Y ".venv\Scripts\pythonw.exe" ".venv\Scripts\HEIC Convert.exe" >nul
)

start "HEIC Convert" ".venv\Scripts\HEIC Convert.exe" "%~dp0app.py" %*
endlocal
