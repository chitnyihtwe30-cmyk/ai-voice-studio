@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo Myanmar AI Voice Studio - LOCAL MODE
 echo ==============================================
echo.
echo This launcher installs dependencies and starts
 echo the single local website + AI backend.
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found.
  echo Install Python 3.11 or 3.12, then run this file again.
  pause
  exit /b 1
)

echo [1/2] Installing/checking dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo.
echo [2/2] Starting local website and AI backend...
echo.
echo Open in Chrome/Edge: http://127.0.0.1:8080
 echo Keep this window open while using the app.
echo.
python local_server.py
if errorlevel 1 goto :fail
exit /b 0

:fail
echo.
echo STARTUP FAILED. Read the error above.
pause
exit /b 1
