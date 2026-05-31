from __future__ import annotations

import base64
import os
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from funasr import AutoModel


MODEL_NAME = os.getenv("FUNASR_MODEL", "paraformer-zh")
VAD_MODEL = os.getenv("FUNASR_VAD_MODEL", "fsmn-vad")
PUNC_MODEL = os.getenv("FUNASR_PUNC_MODEL", "ct-punc")

app = FastAPI(title="FunASR Local STT")


class Base64Request(BaseModel):
    audio_base64: str


@lru_cache(maxsize=1)
def get_model() -> AutoModel:
    return AutoModel(
        model=MODEL_NAME,
        vad_model=VAD_MODEL,
        punc_model=PUNC_MODEL,
        disable_update=True,
    )


def extract_text(result: Any) -> str:
    if isinstance(result, list):
        return "".join(extract_text(item) for item in result).strip()
    if isinstance(result, dict):
        text = result.get("text")
        if isinstance(text, str):
            return text.strip()
        return "".join(extract_text(value) for value in result.values()).strip()
    if isinstance(result, str):
        return result.strip()
    return ""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/asr")
async def asr(file: UploadFile = File(...)) -> dict[str, str]:
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    data = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        result = get_model().generate(input=tmp_path)
        return {"text": extract_text(result)}
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


@app.post("/asr_base64")
async def asr_base64(payload: Base64Request) -> dict[str, str]:
    raw = base64.b64decode(payload.audio_base64)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(raw)
        tmp_path = tmp.name

    try:
        result = get_model().generate(input=tmp_path)
        return {"text": extract_text(result)}
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
