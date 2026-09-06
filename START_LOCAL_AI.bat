@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo AI Voice Studio - LOCAL WEBSITE + AI
echo ==============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Run setup_local_ai.bat first.
  pause
  exit /b 1
)

if not exist "index.html" (
  echo index.html was not found. Make sure this BAT file is in the repo root.
  pause
  exit /b 1
)

if not exist "local_server.py" (
  echo local_server.py was not found.
  pause
  exit /b 1
)

python check_local_ai.py
if errorlevel 1 (
  echo.
  echo Environment check failed. Run setup_local_ai.bat first.
  pause
  exit /b 1
)

echo.
echo Starting local AI server...
echo.
echo Browser: http://127.0.0.1:8080
echo TTS:     http://127.0.0.1:8080/api/tts/health
echo Clone:   http://127.0.0.1:8080/api/clone/health
echo.
echo Keep this window open while using the website.
echo.
python local_server.py

if errorlevel 1 (
  echo.
  echo Local server stopped with an error.
  pause
)
