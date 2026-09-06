@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo AI Voice Studio - LOCAL AI SETUP
 echo ==============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found.
  echo Install Python 3.11 or 3.12, then run this file again.
  pause
  exit /b 1
)

python --version
if errorlevel 1 exit /b 1

echo.
echo [1/4] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 goto :fail

echo.
echo [2/4] Installing AI Voice Studio dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo.
echo [3/4] Checking Python modules...
python -c "import torch, transformers, flask, librosa, soundfile; print('Core modules OK'); print('Torch:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"
if errorlevel 1 goto :fail

echo.
echo [4/4] Setup complete.
echo First generation may download the Myanmar TTS model and VoxCPM2 model.
echo VoxCPM2 is a large model and works best on a PC with a supported GPU.
echo.
echo Now run START_LOCAL_AI.bat
pause
exit /b 0

:fail
echo.
echo SETUP FAILED.
echo Check the error above and run this file again after fixing it.
pause
exit /b 1
