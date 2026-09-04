# AI Voice Studio — Free XTTS Voice Clone (Google Colab)

This backend uses Coqui XTTS-v2 for voice cloning. It can clone a permitted voice sample, but XTTS-v2 does not support Burmese (`my`) as a synthesis language.

## 1. Open Google Colab

Create a new notebook and enable a GPU if Colab offers one:

**Runtime → Change runtime type → GPU**

## 2. Install

Run this cell:

```bash
!pip -q install TTS fastapi uvicorn[standard] python-multipart
!apt-get -qq update && apt-get -qq install -y ffmpeg
```

If the TTS installation fails because of Python-version compatibility, use a Python 3.11 Colab/runtime environment.

## 3. Download the backend

Run:

```bash
!wget -q https://raw.githubusercontent.com/chitnyihtwe30-cmyk/ai-voice-studio/main/clone_backend.py -O clone_backend.py
```

## 4. Start the API

Run:

```bash
!uvicorn clone_backend:app --host 0.0.0.0 --port 8000
```

Keep this cell running.

## 5. Public URL

For a temporary public URL, use a Cloudflare Quick Tunnel in another Colab cell:

```bash
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared
!chmod +x cloudflared
!./cloudflared tunnel --url http://127.0.0.1:8000
```

Copy the `https://....trycloudflare.com` URL shown by cloudflared.

## 6. Connect the website

In AI Voice Studio → **Clone အသံ**, put that URL into **Clone Backend URL**.

The clone endpoint is:

```text
<YOUR_CLOUDFLARE_URL>/clone
```

The health check is:

```text
<YOUR_CLOUDFLARE_URL>/health
```

## Important

- Use only your own voice or a voice for which you have permission.
- XTTS-v2 supports 17 languages, including English, but not Burmese.
- For Burmese voice cloning, a different multilingual model/backend is required.
- A free Colab runtime can disconnect or stop, so the temporary URL will not be permanent.
