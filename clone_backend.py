import os
import tempfile
from pathlib import Path

import torch
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse
from TTS.api import TTS

app = FastAPI(title="AI Voice Studio XTTS Clone Backend")

MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"Loading XTTS-v2 on {DEVICE}...")
tts = TTS(MODEL_NAME).to(DEVICE)
print("XTTS-v2 ready")

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

    # XTTS-v2 supports a fixed set of languages; Burmese (my) is not one of them.
    supported = {"en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko", "hi"}
    language = language.lower().strip()
    if language not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"XTTS-v2 does not support language '{language}'. Supported: {', '.join(sorted(supported))}"
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

        return FileResponse(
            path=str(output_path),
            media_type="audio/wav",
            filename="cloned-voice.wav",
        )
