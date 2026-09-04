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


@app.get("/health")
def health():
    return {"ok": True, "service": "xtts-v2-clone", "device": DEVICE}


@app.post("/clone")
async def clone(
    file: UploadFile = File(...),
    text: str = Form(...),
    language: str = Form("en"),
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    language = language.lower().strip()
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"XTTS-v2 does not support language '{language}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_LANGUAGES))}"
            ),
        )

    suffix = Path(file.filename or "sample.wav").suffix or ".wav"
    with tempfile.TemporaryDirectory() as tmp:
        sample_path = Path(tmp) / f"sample{suffix}"
        output_path = Path(tmp) / "cloned.wav"
        sample_path.write_bytes(await file.read())

        try:
            tts.tts_to_file(
                text=text.strip(),
                speaker_wav=str(sample_path),
                language=language,
                file_path=str(output_path),
                split_sentences=True,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"XTTS generation failed: {exc}")

        # Read the generated WAV before TemporaryDirectory is removed.
        audio = output_path.read_bytes()

    return Response(
        content=audio,
        media_type="audio/wav",
        headers={"Content-Disposition": 'inline; filename="cloned-voice.wav"'},
    )
