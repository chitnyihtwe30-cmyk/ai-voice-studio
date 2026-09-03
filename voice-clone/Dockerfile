FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

EXPOSE 7860

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]
