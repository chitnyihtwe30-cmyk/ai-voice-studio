import os
import subprocess
import tempfile
from pathlib import Path

import torch
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from voxcpm import VoxCPM
import soundfile as sf

app = FastAPI(title="AI Voice Studio Burmese VoxCPM2 Clone Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = "openbmb/VoxCPM2"

print(f"Loading VoxCPM2 on {DEVICE}...")
model = VoxCPM.from_pretrained(MODEL_NAME, load_denoiser=False)
print("VoxCPM2 ready - Burmese voice cloning enabled")


def convert_to_wav(input_path: Path, output_path: Path) -> None:
    """Convert uploaded MP4/audio to mono 16 kHz WAV for VoxCPM2."""
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(input_path),
            "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
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
        "service": "voxcpm2-burmese-clone",
        "device": DEVICE,
        "mp4": True,
        "burmese": True,
        "model": MODEL_NAME,
    }


@app.post("/clone")
async def clone(
    file: UploadFile | None = File(None),
    audio: UploadFile | None = File(None),
    sample: UploadFile | None = File(None),
    text: str = Form(...),
    language: str = Form("my"),
    speed: str | None = Form(None),
):
    incoming = file or audio or sample
    if incoming is None:
        raise HTTPException(status_code=400, detail="voice sample file is required")
    if not text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    # VoxCPM2 automatically detects supported languages from the text.
    # Burmese is supported directly, so no language tag is required.
    original_name = incoming.filename or "sample.wav"
    suffix = Path(original_name).suffix.lower() or ".wav"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        input_path = tmp_dir / f"upload{suffix}"
        sample_path = tmp_dir / "sample.wav"
        output_path = tmp_dir / "cloned.wav"
        input_path.write_bytes(await incoming.read())

        try:
            convert_to_wav(input_path, sample_path)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Audio conversion failed: {exc}")

        try:
            kwargs = {
                "text": text.strip(),
                "reference_wav_path": str(sample_path),
            }
            if speed:
                kwargs["text"] = f"(speaking speed {speed}){text.strip()}"

            wav = model.generate(**kwargs)
            sf.write(str(output_path), wav, model.tts_model.sample_rate)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"VoxCPM2 generation failed: {exc}")

        audio_bytes = output_path.read_bytes()

    return Response(
        content=audio_bytes,
        media_type="audio/wav",
        headers={"Content-Disposition": 'inline; filename="cloned-voice.wav"'},
    )
