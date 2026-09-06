# AI Voice Studio — Local AI Setup

This repository is prepared to run the AI Voice Studio website locally.

## What it includes

- English + Myanmar UI
- Real Myanmar AI TTS using `facebook/mms-tts-mya`
- Real Myanmar voice cloning using `openbmb/VoxCPM2`
- Reference voice upload for cloning
- Myanmar text up to 5,000 characters
- Speed control from 0.5× to 2.0×
- Local single-entry website at `http://127.0.0.1:8080`
- TTS API mounted at `/api/tts`
- Voice Clone API mounted at `/api/clone`

## Windows quick start

1. Download/clone this repository.
2. Install **Python 3.11 or 3.12** and make sure `python` works in Command Prompt.
3. Double-click `setup_local_ai.bat` once.
4. After setup finishes, double-click `START_LOCAL_AI.bat`.
5. Open `http://127.0.0.1:8080` in Chrome or Edge.
6. Wait for the page to show **LOCAL AI CONNECTED**.
7. Use Myanmar AI Voice for TTS, or Myanmar Voice Clone with a reference WAV/MP3/M4A file.

`run_ai_voice_studio.bat` is also available as the combined setup/check + start launcher.

## First run

The AI models are downloaded automatically when they are first loaded. The Myanmar TTS model is much smaller than VoxCPM2. VoxCPM2 is a large model, so the first clone request can take a while and requires substantially more RAM/VRAM.

For reliable VoxCPM2 cloning, use a PC with a suitable GPU. A normal Android phone should not be expected to run the full VoxCPM2 model locally.

## Important

This is **local website mode**, not a Vercel-only frontend. The browser page and API gateway run on the same computer at `127.0.0.1:8080`.

A fully offline phone-only version is a separate optimization project; the current VoxCPM2 model is too large to treat ordinary Android hardware as a reliable inference target.
