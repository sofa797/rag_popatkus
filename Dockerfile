FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/

RUN mkdir -p /app/shared/data/pdf /app/shared/data/parsed /app/shared/data/qdrant

EXPOSE 8001 7860

CMD python loader_html.py && python build_index.py && uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 & python frontend/gradio_app.py
