import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from TTS.api import TTS

MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
SUPPORTED = {"my", "en"}

app = FastAPI(title="AI Voice Studio Voice Clone API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["*"]
)

tts = None

def get_tts():
    global tts
    if tts is None:
        tts = TTS(MODEL)
    return tts

@app.get("/health")
def health():
    return {"ok": True, "model": MODEL}

@app.post("/clone")
async def clone(
    text: str = Form(...),
    language: str = Form("my"),
    speaker_wav: UploadFile = File(...),
):
    text = text.strip()
    language = language.strip().lower()
    if not text:
        raise HTTPException(400, "Text is required")
    if len(text) > 5000:
        raise HTTPException(400, "Text must be 5,000 characters or less")
    if language not in SUPPORTED:
        raise HTTPException(400, "Language must be my or en")

    suffix = Path(speaker_wav.filename or "sample.wav").suffix or ".wav"
    with tempfile.TemporaryDirectory() as td:
        sample = os.path.join(td, "sample" + suffix)
        output = os.path.join(td, "voice_clone.wav")
        with open(sample, "wb") as f:
            f.write(await speaker_wav.read())
        try:
            get_tts().tts_to_file(
                text=text,
                speaker_wav=sample,
                language=language,
                file_path=output,
            )
        except Exception as exc:
            raise HTTPException(500, f"Voice cloning failed: {exc}") from exc

        # Return the generated file before the temporary directory is removed.
        # FastAPI reads the response asynchronously, so copy it to a persistent temp file.
        fd, persistent = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        with open(output, "rb") as src, open(persistent, "wb") as dst:
            dst.write(src.read())

    return FileResponse(
        persistent,
        media_type="audio/wav",
        filename="voice_clone.wav",
        background=None,
    )
