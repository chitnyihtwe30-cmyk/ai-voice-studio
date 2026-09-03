# Voice Clone Backend

This folder contains a separate backend for voice cloning. GitHub Pages can host the frontend, but it cannot run the Python voice-cloning model itself.

## Model

The example uses Coqui XTTS-v2. Use only voice samples you own or have permission to clone.

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

The API listens on port 7860 and exposes `POST /clone` with:
- `text`: text to speak
- `speaker_wav`: reference voice sample (`wav`, `mp3`, `m4a`, etc.)
- `language`: `my` or `en`

The response is a WAV audio file.

## Important

The Gemini TTS API does not accept an arbitrary voice recording as a custom cloned voice; it uses prebuilt voices. The clone feature therefore needs this separate backend. See Google's current TTS documentation: https://ai.google.dev/gemini-api/docs/speech-generation
