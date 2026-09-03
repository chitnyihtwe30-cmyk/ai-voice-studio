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

MODEL = "openbmb/VoxCPM2"
app = FastAPI(title="AI Voice Studio Burmese Voice Clone")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
model = None

def get_model():
    global model
    if model is None:
        model = VoxCPM.from_pretrained(MODEL, load_denoiser=False)
    return model

def cleanup(path):
    try: os.remove(path)
    except FileNotFoundError: pass

def to_wav(src, dst):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg: raise RuntimeError("ffmpeg is not installed")
    r = subprocess.run([ffmpeg, "-y", "-i", src, "-ar", "16000", "-ac", "1", dst], capture_output=True, text=True)
    if r.returncode != 0: raise RuntimeError("Audio conversion failed")

@app.get("/")
def root():
    return {"ok": True, "service": "AI Voice Studio Burmese Voice Clone", "model": MODEL}

@app.get("/health")
def health():
    return {"ok": True, "model": MODEL, "language": "Burmese (my)", "voice_cloning": True}

@app.post("/clone")
async def clone(text: str = Form(...), audio: UploadFile = File(...)):
    text = text.strip()
    if not text: raise HTTPException(400, "Text is required")
    if len(text) > 5000: raise HTTPException(400, "Text must be 5000 characters or less")
    suffix = Path(audio.filename or "sample.wav").suffix.lower() or ".wav"
    if suffix not in {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".webm"}:
        raise HTTPException(400, "Unsupported audio format")
    data = await audio.read(25 * 1024 * 1024 + 1)
    if len(data) > 25 * 1024 * 1024: raise HTTPException(413, "Audio file must be 25 MB or smaller")
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "input" + suffix)
        wav_path = os.path.join(td, "sample.wav")
        out = os.path.join(td, "clone.wav")
        with open(src, "wb") as f: f.write(data)
        try:
            to_wav(src, wav_path)
            m = get_model()
            audio_out = m.generate(text=text, reference_wav_path=wav_path, cfg_value=2.0, inference_timesteps=10, max_len=600, normalize=False, denoise=False, retry_badcase=True, retry_badcase_max_times=2)
            import soundfile as sf
            sf.write(out, audio_out, m.tts_model.sample_rate)
        except Exception as e:
            raise HTTPException(500, f"Voice cloning failed: {e}")
        fd, persistent = tempfile.mkstemp(suffix=".wav"); os.close(fd)
        with open(out, "rb") as a, open(persistent, "wb") as b: b.write(a.read())
    return FileResponse(persistent, media_type="audio/wav", filename="burmese_voice_clone.wav", background=BackgroundTask(cleanup, persistent))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "7860")))
