#!/bin/bash
set -e

python loader_html.py
python build_index.py

uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 &

exec python frontend/gradio_app.py