FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FUNASR_MODEL=paraformer-zh \
    FUNASR_VAD_MODEL=fsmn-vad \
    FUNASR_PUNC_MODEL=ct-punc

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libsndfile1 curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY app /app/app

EXPOSE 10095

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "10095"]
