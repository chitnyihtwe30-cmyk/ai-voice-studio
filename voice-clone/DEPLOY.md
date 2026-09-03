# Voice Clone Backend Deployment

The frontend can be hosted as a static website, but XTTS-v2 needs a Python server with enough CPU/RAM and disk for the model.

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

For a public deployment, set the frontend's **Backend URL** to the public HTTPS URL of this server.

## Free-hosting note

Do not assume a static hosting service can run this backend. A static host can serve `index.html`, but the XTTS-v2 Python process must run on a compute service that permits the required dependencies and resources.
