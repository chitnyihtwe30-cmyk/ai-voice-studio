from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from voxcpm import VoxCPM
import os, tempfile, io, re
import soundfile as sf

MODEL_ID = "openbmb/VoxCPM2"
app = Flask(__name__)
CORS(app)

print(f"Loading Myanmar-capable voice clone model: {MODEL_ID}")
model = VoxCPM.from_pretrained(MODEL_ID, load_denoiser=False)
print("VoxCPM2 voice clone model ready")

MYANMAR_RE = re.compile(r"[\u1000-\u109F\uAA60-\uAA7F]")

def is_myanmar_text(text: str) -> bool:
    return bool(MYANMAR_RE.search(text))

@app.get('/health')
def health():
    return jsonify({
        'ok': True,
        'model': MODEL_ID,
        'feature': 'Myanmar Voice Clone',
        'language': 'Myanmar',
        'ready': True,
        'sample_rate': int(model.tts_model.sample_rate)
    })

@app.post('/clone')
def clone():
    if 'audio' not in request.files:
        return jsonify({'error': 'Reference voice audio is required.'}), 400

    text = (request.form.get('text') or '').strip()
    speed = float(request.form.get('speed', '1.0'))

    if not text:
        return jsonify({'error': 'Myanmar text is required.'}), 400
    if len(text) > 5000:
        return jsonify({'error': 'Maximum 5,000 characters.'}), 400
    if not is_myanmar_text(text):
        return jsonify({'error': 'Myanmar Voice Clone accepts Myanmar text only.'}), 400
    speed = max(0.5, min(2.0, speed))

    suffix = os.path.splitext(request.files['audio'].filename or '.wav')[1] or '.wav'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as ref:
        request.files['audio'].save(ref.name)
        ref_path = ref.name

    try:
        # Speed/style is expressed as an instruction so the cloned timbre is preserved.
        style = '' if speed == 1.0 else f'(speaking at {speed:.1f}x speed)'
        prompt = style + text

        wav = model.generate(
            text=prompt,
            reference_wav_path=ref_path,
            cfg_value=2.0,
            inference_timesteps=10,
            normalize=True,
            denoise=False,
            retry_badcase=True,
            retry_badcase_max_times=2,
        )

        buf = io.BytesIO()
        sf.write(buf, wav, int(model.tts_model.sample_rate), format='WAV')
        buf.seek(0)
        return send_file(buf, mimetype='audio/wav', as_attachment=False, download_name='myanmar-cloned-voice.wav')
    finally:
        try:
            os.unlink(ref_path)
        except OSError:
            pass

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('CLONE_PORT', '7862')), debug=False)
