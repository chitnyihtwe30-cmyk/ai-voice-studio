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

### Render

Render currently offers free web services, including Python/FastAPI services and Docker deployments. Free services can sleep after 15 minutes without inbound traffic and have limited CPU/RAM, so XTTS-v2 may be slow or may fail if the model exceeds the available resources. Use Render mainly as a test option.

For deployment, create a **Web Service**, connect this GitHub repository, and set the service root directory to `voice-clone`. Use the Docker runtime or the Python runtime with the project's requirements. After deployment, verify `/health` before putting the URL into the frontend.

### Hugging Face

Static Spaces cannot run this FastAPI backend. Hugging Face currently provides free ZeroGPU hosting for eligible personal accounts, but ZeroGPU Spaces are Gradio-only, so this FastAPI/Docker backend cannot be moved there unchanged. A separate Gradio version would be needed.

## Safety

Only clone voices that you own or have permission to use. Do not use the service to impersonate someone without consent.
