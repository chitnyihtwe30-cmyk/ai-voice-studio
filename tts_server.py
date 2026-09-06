from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from transformers import VitsModel, AutoTokenizer
import torch
import scipy.io.wavfile as wavfile
import numpy as np
import io
import os

MODEL_ID = "facebook/mms-tts-mya"
app = Flask(__name__)
CORS(app)

print(f"Loading Myanmar TTS model: {MODEL_ID}")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = VitsModel.from_pretrained(MODEL_ID)
model.eval()
print("Myanmar TTS model ready")

@app.get("/health")
def health():
    return jsonify({"ok": True, "model": MODEL_ID, "language": "Myanmar", "offline": True})

@app.post("/tts")
def tts():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    speed = float(data.get("speed", 1.0))
    if not text:
        return jsonify({"error": "Myanmar text is required"}), 400
    if len(text) > 5000:
        return jsonify({"error": "Maximum 5,000 characters"}), 400
    speed = max(0.5, min(2.0, speed))

    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        waveform = model(**inputs).waveform.squeeze().cpu().numpy()

    # Change playback speed without changing the model itself.
    if speed != 1.0:
        target_len = max(1, int(len(waveform) / speed))
        old_x = np.linspace(0, 1, len(waveform), endpoint=False)
        new_x = np.linspace(0, 1, target_len, endpoint=False)
        waveform = np.interp(new_x, old_x, waveform).astype(np.float32)

    waveform = np.clip(waveform, -1.0, 1.0)
    audio = (waveform * 32767).astype(np.int16)
    buf = io.BytesIO()
    wavfile.write(buf, int(model.config.sampling_rate), audio)
    buf.seek(0)
    return send_file(buf, mimetype="audio/wav", as_attachment=False, download_name="myanmar-ai-voice.wav")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("TTS_PORT", "7861")), debug=False)
