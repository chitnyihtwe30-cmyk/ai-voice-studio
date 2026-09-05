import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from voxcpm import VoxCPM

MODEL = os.getenv("TTS_MODEL", "openbmb/VoxCPM2")
MAX_TEXT = 5000
MAX_AUDIO_BYTES = 25 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    ".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".webm", ".mp4"
}

app = FastAPI(title="AI Voice Studio — Burmese Voice Clone API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"]
)

model = None


def get_model():
    global model
    if model is None:
        model = VoxCPM.from_pretrained(MODEL, load_denoiser=False)
    return model


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
        [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-i", source,
            "-vn", "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
            target,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or "Could not convert the uploaded media to WAV"
        raise RuntimeError(detail)


@app.get("/health")
def health():
    return {
        "ok": True,
        "model": MODEL,
        "language": "Burmese (my)",
        "voice_cloning": True,
        "mp4": True,
        "max_text": MAX_TEXT,
        "max_audio_mb": MAX_AUDIO_BYTES // (1024 * 1024),
    }


@app.post("/clone")
async def clone(
    text: str = Form(...),
    audio: UploadFile | None = File(None),
    file: UploadFile | None = File(None),
    sample: UploadFile | None = File(None),
):
    # Accept the common field names used by different frontend versions.
    incoming = audio or file or sample
    if incoming is None:
        raise HTTPException(400, "Voice sample file is required")

    text = text.strip()
    if not text:
        raise HTTPException(400, "Text is required")
    if len(text) > MAX_TEXT:
        raise HTTPException(400, f"Text must be {MAX_TEXT:,} characters or less")

    suffix = Path(incoming.filename or "sample.wav").suffix.lower() or ".wav"
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Unsupported audio/video format")

    with tempfile.TemporaryDirectory() as td:
        uploaded = os.path.join(td, "uploaded" + suffix)
        sample_wav = os.path.join(td, "sample.wav")
        output = os.path.join(td, "voice_clone.wav")

        data = await incoming.read(MAX_AUDIO_BYTES + 1)
        if len(data) > MAX_AUDIO_BYTES:
            raise HTTPException(413, "Voice sample must be 25 MB or smaller")
        if not data:
            raise HTTPException(400, "Voice sample file is empty")

        with open(uploaded, "wb") as f:
            f.write(data)

        try:
            convert_to_wav(uploaded, sample_wav)
            current_model = get_model()
            wav = current_model.generate(
                text=text,
                reference_wav_path=sample_wav,
                cfg_value=2.0,
                inference_timesteps=10,
                max_len=600,
                normalize=False,
                denoise=False,
                retry_badcase=True,
                retry_badcase_max_times=2,
            )

            import soundfile as sf
            sf.write(output, wav, current_model.tts_model.sample_rate)
        except Exception as exc:
            raise HTTPException(500, f"Burmese voice cloning failed: {exc}") from exc

        fd, persistent = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        with open(output, "rb") as src, open(persistent, "wb") as dst:
            dst.write(src.read())

    return FileResponse(
        persistent,
        media_type="audio/wav",
        filename="burmese_voice_clone.wav",
        background=BackgroundTask(remove_file, persistent),
    )
