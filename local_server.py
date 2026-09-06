from pathlib import Path
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple
from flask import Flask, send_from_directory

# Local single-entry website: http://127.0.0.1:8080
# It mounts the real Myanmar TTS and VoxCPM2 clone servers under /api.
from tts_server import app as tts_app
from clone_server import app as clone_app

ROOT = Path(__file__).resolve().parent
web_app = Flask(__name__, static_folder=str(ROOT), static_url_path='')

@web_app.get('/')
def index():
    return send_from_directory(ROOT, 'index.html')

@web_app.get('/health')
def health():
    return {'ok': True, 'mode': 'local', 'api': '/api'}

application = DispatcherMiddleware(web_app, {
    '/api/tts': tts_app,
    '/api/clone': clone_app,
})

if __name__ == '__main__':
    print('AI Voice Studio LOCAL')
    print('Open: http://127.0.0.1:8080')
    print('Myanmar TTS: /api/tts')
    print('Myanmar Voice Clone: /api/clone')
    run_simple('127.0.0.1', 8080, application, threaded=True, use_reloader=False)
