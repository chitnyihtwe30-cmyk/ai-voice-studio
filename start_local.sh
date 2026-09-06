#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "=============================================="
echo "AI Voice Studio - LOCAL AI"
echo "=============================================="
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 was not found. Install Python 3.11 or 3.12."
  exit 1
fi

python3 -m pip install -r requirements.txt
python3 check_local_ai.py

echo
echo "Starting local website..."
echo "Open: http://127.0.0.1:8080"
echo "Keep this terminal open while using the website."
echo
python3 local_server.py
