# Voice Clone Backend Deployment

The AI Voice Studio frontend can be hosted as a static website, while the VoxCPM2 voice-clone API must run on a Python compute service with enough CPU/RAM/disk for the model. GPU is strongly recommended for practical response times.

## Backend API

The canonical backend is `voice-clone/app.py`.

Endpoints:

- `GET /health` — service/model health information
- `POST /clone` — accepts `text` plus an audio/video upload in the `audio`, `file`, or `sample` field

Supported sample formats include WAV, MP3, M4A, FLAC, OGG, AAC, WebM, and MP4. MP4/video uploads are converted to mono 16 kHz WAV with FFmpeg before cloning.

The API accepts up to 5,000 text characters and a 25 MB reference-media file.

## Docker

Build and run the backend with the included Dockerfile:

```bash
docker build -t ai-voice-clone ./voice-clone
docker run --rm -p 7860:7860 ai-voice-clone
```

Then test:

```text
http://localhost:7860/health
```

For a public deployment, set the frontend's **Clone Backend URL** to the public HTTPS URL of this server.

## Production notes

Do not put the Gemini API key or other server secrets in the static frontend. The clone backend currently does not require a secret for local testing, but a production deployment should add authentication/rate limiting before exposing a public GPU endpoint.

A static hosting service can serve `index.html`, but it cannot run this Python model server. Use a compute service that supports Docker/Python and provides enough memory for VoxCPM2.

### Render

Render can run Python/FastAPI services and Docker deployments. Low-resource/free instances may sleep or lack enough memory/compute for VoxCPM2, so treat them as testing options and verify `/health` and an actual `/clone` request after deployment.

### Hugging Face

A static Space cannot run this FastAPI backend unchanged. If using a Hugging Face Space, the deployment must use a compatible runtime/application design and sufficient compute for VoxCPM2.

## Safety

Only clone voices that you own or have permission to use. Do not use the service to impersonate someone without consent.
