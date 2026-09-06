import importlib.util
import platform
import sys

REQUIRED = [
    'torch', 'transformers', 'accelerate', 'scipy', 'soundfile',
    'sentencepiece', 'flask', 'flask_cors', 'voxcpm', 'librosa'
]

print('AI Voice Studio - LOCAL AI CHECK')
print('Python:', sys.version.split()[0])
print('OS:', platform.platform())
print()

missing = []
for name in REQUIRED:
    if importlib.util.find_spec(name) is None:
        missing.append(name)

if missing:
    print('MISSING MODULES:', ', '.join(missing))
    print('Run: python -m pip install -r requirements.txt')
    raise SystemExit(1)

import torch
print('Torch:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('GPU:', torch.cuda.get_device_name(0))
else:
    print('GPU: CPU mode')

print('\nAll required Python modules are installed.')
print('Next: run START_LOCAL_AI.bat (Windows) or ./start_local.sh (Linux/macOS).')
