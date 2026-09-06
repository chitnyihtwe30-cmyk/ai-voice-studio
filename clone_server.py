from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import io, os, tempfile

app = Flask(__name__)
CORS(app)

MODEL_ID = os.environ.get("CLONE_MODEL", "openbmb/VoxCPM2")
MAX_CHARS = 5000
_model = None
_tokenizer = None
_load_error = None


def load_model():
    global _model, _tokenizer, _load_error
    if _model is not None:
        return _model
    try:
        import torch
        from voxcpm import VoxCPM
        _model = VoxCPM.from_pretrained(MODEL_ID)
        _tokenizer = torch
        _load_error = None
        return _model
    except Exception as exc:
        _load_error = str(exc)
        raise


@app.get('/health')
def health():
    ready = _model is not None
    return jsonify({
        'ok': True,
        'feature': 'Myanmar Voice Clone',
        'language': 'Myanmar',
        'model': MODEL_ID,
        'ready': ready,
        'reason': None if ready else (_load_error or 'Model will load on first clone request.')
    })


@app.post('/clone')
def clone():
    if 'audio' not in request.files:
        return jsonify({'error': 'Reference voice audio is required.'}), 400
    audio = request.files['audio']
    text = (request.form.get('text') or '').strip()
    if not text:
        return jsonify({'error': 'Myanmar text is required.'}), 400
    if len(text) > MAX_CHARS:
        return jsonify({'error': f'Maximum {MAX_CHARS:,} characters.'}), 400

    ref_path = None
    out_path = None
    try:
        load_model()
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as ref:
            audio.save(ref.name)
            ref_path = ref.name
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as out:
            out_path = out.name

        # VoxCPM2 zero-shot voice cloning: reference audio + Myanmar text.
        # The model itself handles the speaker/style conditioning.
        result = _model.generate(
            text=text,
            prompt_wav_path=ref_path,
            output_path=out_path,
        )

        if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
            # Some VoxCPM builds return waveform instead of writing output.
            if result is None:
                raise RuntimeError('VoxCPM2 returned no audio output.')
            import soundfile as sf
            import numpy as np
            waveform = result.detach().float().cpu().numpy() if hasattr(result, 'detach') else np.asarray(result)
            waveform = np.squeeze(waveform)
            sf.write(out_path, waveform, 48000)

        return send_file(out_path, mimetype='audio/wav', as_attachment=False, download_name='myanmar-voice-clone.wav')
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
    app.run(host='127.0.0.1', port=int(os.environ.get('CLONE_PORT', '7862')), debug=False)
