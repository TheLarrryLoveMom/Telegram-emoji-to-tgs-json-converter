@echo off
setlocal

REM Change to project root
cd /d "%~dp0"

REM Activate venv if present
if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
)

REM Load env from .env by default
set ENV_FILE=%~dp0.env
set PYTHONUNBUFFERED=1

python -m bot.main

endlocal