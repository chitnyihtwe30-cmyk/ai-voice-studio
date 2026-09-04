import os
import subprocess
import tempfile
from pathlib import Path

import torch
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import Response
from TTS.api import TTS

app = FastAPI(title="AI Voice Studio XTTS Clone Backend")

MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading XTTS-v2 on {DEVICE}...")
tts = TTS(MODEL_NAME).to(DEVICE)
print("XTTS-v2 ready")

SUPPORTED_LANGUAGES = {
    "en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl",
    "cs", "ar", "zh-cn", "ja", "hu", "ko", "hi"
}


def convert_to_wav(input_path: Path, output_path: Path) -> None:
    """Convert an uploaded MP4/audio sample to mono WAV for XTTS."""
    ffmpeg = "ffmpeg"
    if os.name == "nt":
        ffmpeg = "ffmpeg.exe"

    result = subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(input_path),
            "-vn", "-ac", "1", "-ar", "22050", "-c:a", "pcm_s16le",
            str(output_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "FFmpeg conversion failed")


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "xtts-v2-clone",
        "device": DEVICE,
        "mp4": True,
        "languages": sorted(SUPPORTED_LANGUAGES),
        "burmese": False,
    }


@app.post("/clone")
async def clone(
    file: UploadFile | None = File(None),
    audio: UploadFile | None = File(None),
    sample: UploadFile | None = File(None),
    text: str = Form(...),
    language: str = Form("en"),
    speed: str | None = Form(None),
):
    incoming = file or audio or sample
    if incoming is None:
        raise HTTPException(status_code=400, detail="voice sample file is required")
    if not text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    language = language.lower().strip()
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"XTTS-v2 does not support language '{language}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_LANGUAGES))}. "
                "Burmese (my) is not supported by XTTS-v2."
            ),
        )

    original_name = incoming.filename or "sample.wav"
    suffix = Path(original_name).suffix.lower() or ".wav"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        input_path = tmp_dir / f"upload{suffix}"
        sample_path = tmp_dir / "sample.wav"
        output_path = tmp_dir / "cloned.wav"
        input_path.write_bytes(await incoming.read())

        try:
            # Always normalize the sample. This also makes MP4 uploads work.
            convert_to_wav(input_path, sample_path)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Audio conversion failed: {exc}")

        try:
            kwargs = {
                "text": text.strip(),
                "speaker_wav": str(sample_path),
                "language": language,
                "file_path": str(output_path),
                "split_sentences": True,
            }
            tts.tts_to_file(**kwargs)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"XTTS generation failed: {exc}")

        audio_bytes = output_path.read_bytes()

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={"Content-Disposition": 'inline; filename="cloned-voice.wav"'},
    )
