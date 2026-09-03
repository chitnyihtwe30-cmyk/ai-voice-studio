import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from TTS.api import TTS

MODEL = os.getenv("TTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2")
# XTTS-v2 officially supports these 17 languages. Burmese (my) is not supported.
SUPPORTED = {"en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko", "hi"}
MAX_TEXT = 5000
MAX_AUDIO_BYTES = 25 * 1024 * 1024

app = FastAPI(title="AI Voice Studio Voice Clone API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"]
)

tts = None


def get_tts():
    global tts
    if tts is None:
        tts = TTS(MODEL)
    return tts


def remove_file(path: str):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def convert_to_wav(source: str, target: str):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required on the server")
    result = subprocess.run(
        [ffmpeg, "-y", "-i", source, "-ar", "22050", "-ac", "1", target],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("Could not convert the uploaded audio to WAV")


@app.get("/health")
def health():
    return {"ok": True, "model": MODEL, "languages": sorted(SUPPORTED)}


@app.post("/clone")
async def clone(
    text: str = Form(...),
    audio: UploadFile = File(...),
    language: str = Form("en"),
):
    text = text.strip()
    language = language.strip().lower()

    if not text:
        raise HTTPException(400, "Text is required")
    if len(text) > MAX_TEXT:
        raise HTTPException(400, f"Text must be {MAX_TEXT:,} characters or less")
    if language not in SUPPORTED:
        raise HTTPException(400, "Unsupported language. XTTS-v2 does not support Burmese (my); use one of the supported language codes.")

    suffix = Path(audio.filename or "sample.wav").suffix.lower() or ".wav"
    allowed = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".webm"}
    if suffix not in allowed:
        raise HTTPException(400, "Unsupported audio format")

    with tempfile.TemporaryDirectory() as td:
        uploaded = os.path.join(td, "uploaded" + suffix)
        sample = os.path.join(td, "sample.wav")
        output = os.path.join(td, "voice_clone.wav")

        data = await audio.read(MAX_AUDIO_BYTES + 1)
        if len(data) > MAX_AUDIO_BYTES:
            raise HTTPException(413, "Audio file must be 25 MB or smaller")
        if not data:
            raise HTTPException(400, "Audio file is empty")

        with open(uploaded, "wb") as f:
            f.write(data)

        try:
            convert_to_wav(uploaded, sample)
            get_tts().tts_to_file(
                text=text,
                speaker_wav=sample,
                language=language,
                file_path=output,
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(500, f"Voice cloning failed: {exc}") from exc

        fd, persistent = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        with open(output, "rb") as src, open(persistent, "wb") as dst:
            dst.write(src.read())

    return FileResponse(
        persistent,
        media_type="audio/wav",
        filename="voice_clone.wav",
        background=BackgroundTask(remove_file, persistent),
    )
