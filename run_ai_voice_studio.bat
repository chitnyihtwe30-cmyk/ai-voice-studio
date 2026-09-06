@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo Myanmar AI Voice Studio - Local Engine Setup
echo ==============================================
echo.

echo [1/3] Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Dependency installation failed.
  pause
  exit /b 1
)

echo.
echo [2/3] Starting Myanmar TTS server on port 7861...
start "Myanmar TTS" cmd /k "cd /d "%~dp0" && python tts_server.py"

echo [3/3] Starting Myanmar VoxCPM2 Voice Clone server on port 7862...
start "Myanmar Voice Clone - VoxCPM2" cmd /k "cd /d "%~dp0" && python clone_server.py"

echo.
echo ==============================================
echo Servers started.
echo Open index.html in Chrome/Edge.
echo TTS:   http://127.0.0.1:7861/health
echo Clone: http://127.0.0.1:7862/health
echo ==============================================
echo.
pause
