from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import io, os, tempfile, subprocess

app = Flask(__name__)
CORS(app)

# Myanmar-only clone service contract.
# This endpoint is intentionally disabled until a compatible local voice-clone
# checkpoint is installed. It prevents the UI from silently falling back to an
# English or browser TTS voice.

@app.get('/health')
def health():
    return jsonify({
        'ok': True,
        'feature': 'Myanmar Voice Clone',
        'language': 'Myanmar',
        'ready': False,
        'reason': 'Install a compatible local Myanmar voice-clone checkpoint.'
    })

@app.post('/clone')
def clone():
    if 'audio' not in request.files:
        return jsonify({'error': 'Reference voice audio is required.'}), 400
    audio = request.files['audio']
    text = (request.form.get('text') or '').strip()
    if not text:
        return jsonify({'error': 'Text is required.'}), 400
    if len(text) > 5000:
        return jsonify({'error': 'Maximum 5,000 characters.'}), 400
    return jsonify({
        'error': 'Myanmar Voice Clone model is not installed yet. The reference audio was received, but no English/browser fallback is used.'
    }), 501

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('CLONE_PORT', '7862')), debug=False)
