#!/bin/bash

set -e

mkdir -p dataset

DATA_ZIP="data.zip"
RELEASE_URL="https://github.com/sofa797/rag_popatkus/releases/download/v0.1-data/data.zip"

if [ -d "data/parsed" ] && [ -f "data/parsed/parsed_pdf.json" ]; then
    echo "files already exist"
else
    if curl -sSfL "$RELEASE_URL" -o "$DATA_ZIP"; then
        python3 -c "import zipfile; zipfile.ZipFile('$DATA_ZIP').extractall('.')"
        rm "$DATA_ZIP"
    else
        echo "download error"
    fi
fi

if [ -d ".venv" ]; then
    echo ".venv already exist"
else
    python3 -m venv .venv
fi

source .venv/bin/activate

pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
