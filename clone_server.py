from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import tempfile

app = Flask(__name__)
CORS(app)

MODEL_ID = os.environ.get("CLONE_MODEL", "openbmb/VoxCPM2")
MAX_CHARS = 5000
_model = None
_load_error = None


def load_model():
    global _model, _load_error
    if _model is not None:
        return _model
    try:
        from voxcpm import VoxCPM
        _model = VoxCPM.from_pretrained(MODEL_ID, load_denoiser=False)
        _load_error = None
        return _model
    except Exception as exc:
        _load_error = str(exc)
        raise


@app.get('/health')
def health():
    return jsonify({
        'ok': True,
        'feature': 'Myanmar Voice Clone',
        'language': 'Myanmar',
        'model': MODEL_ID,
        'ready': _model is not None,
        'reason': None if _model is not None else (_load_error or 'Model loads on first clone request.')
    })


def speed_audio(wav, sample_rate, speed):
    speed = max(0.5, min(2.0, float(speed)))
    if abs(speed - 1.0) < 0.001:
        return wav
    try:
        import numpy as np
        import librosa
        audio = wav.detach().float().cpu().numpy() if hasattr(wav, 'detach') else np.asarray(wav)
        audio = np.squeeze(audio)
        return librosa.effects.time_stretch(audio, rate=speed)
    except Exception as exc:
        raise RuntimeError(f'Audio speed processing failed: {exc}')


@app.post('/clone')
def clone():
    if 'audio' not in request.files:
        return jsonify({'error': 'Reference voice audio is required.'}), 400

    text = (request.form.get('text') or '').strip()
    if not text:
        return jsonify({'error': 'Myanmar text is required.'}), 400
    if len(text) > MAX_CHARS:
        return jsonify({'error': f'Maximum {MAX_CHARS:,} characters.'}), 400

    # Keep this engine Myanmar-focused: reject text that contains no Myanmar characters.
    if not any('\u1000' <= ch <= '\u109f' or '\uaa60' <= ch <= '\uaa7f' for ch in text):
        return jsonify({'error': 'Myanmar text is required. English-only text is not supported.'}), 400

    ref_path = None
    out_path = None
    try:
        model = load_model()

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as ref:
            request.files['audio'].save(ref.name)
            ref_path = ref.name

        import soundfile as sf

        # VoxCPM2 reference-audio zero-shot cloning. The reference speaker is
        # used to condition the generated Myanmar speech.
        wav = model.generate(
            text=text,
            reference_wav_path=ref_path,
            cfg_value=2.0,
            inference_timesteps=10,
        )

        sample_rate = int(getattr(model.tts_model, 'sample_rate', 48000))
        speed = request.form.get('speed', '1.0')
        wav = speed_audio(wav, sample_rate, speed)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as out:
            out_path = out.name
        sf.write(out_path, wav, sample_rate)

        return send_file(
            out_path,
            mimetype='audio/wav',
            as_attachment=False,
            download_name='myanmar-voice-clone.wav'
        )
    except Exception as exc:
        return jsonify({
            'error': 'Myanmar Voice Clone failed.',
            'details': str(exc),
            'model': MODEL_ID
        }), 500
    finally:
        for p in (ref_path, out_path):
            if p:
                try:
                    os.remove(p)
                except OSError:
                    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('CLONE_PORT', '7862')), debug=False)
