#!/usr/bin/env python3
"""
FastAPI Server for Vietnamese ASR (Zipformer-30M-RNNT)
Provides REST API endpoint for Xiaozhi STT integration
"""

import tempfile
import os
from pathlib import Path

import numpy as np
import soundfile as sf
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException

import sherpa_onnx

app = FastAPI(title="Vietnamese ASR - Zipformer-30M-RNNT", version="1.0.0")


def _get_bool(key: str, default: bool = False) -> bool:
    return os.environ.get(key, str(default)).lower() in ("1", "true", "yes")


MODEL_DIR = Path(os.environ.get("MODEL_PATH", "/app/model"))
USE_INT8 = _get_bool("USE_INT8", False)
_suffix = ".int8.onnx" if USE_INT8 else ".onnx"
_base = "epoch-20-avg-10"
ENCODER_PATH = MODEL_DIR / f"encoder-{_base}{_suffix}"
DECODER_PATH = MODEL_DIR / f"decoder-{_base}{_suffix}"
JOINER_PATH = MODEL_DIR / f"joiner-{_base}{_suffix}"
# The BPE vocab in this HF repo is `config.json` (NOT tokens.txt).
TOKENS_PATH = MODEL_DIR / "config.json"
HF_MODEL_ID = os.environ.get("HF_MODEL_ID", "hynt/Zipformer-30M-RNNT-6000h")

recognizer = None


def download_model() -> None:
    """Download the model from HuggingFace if missing (idempotent)."""
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("ERROR: huggingface_hub not installed — cannot auto-download model.")
        raise

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading model {HF_MODEL_ID} → {MODEL_DIR}")
    allow = ["*.int8.onnx", "config.json", "bpe.model"] if USE_INT8 else ["*.onnx", "config.json", "bpe.model"]
    ignore = [] if USE_INT8 else ["*.int8.onnx"]
    snapshot_download(
        repo_id=HF_MODEL_ID,
        local_dir=str(MODEL_DIR),
        allow_patterns=allow,
        ignore_patterns=ignore,
    )


def ensure_model() -> None:
    required = [ENCODER_PATH, DECODER_PATH, JOINER_PATH, TOKENS_PATH]
    missing = [p for p in required if not p.exists()]
    if missing:
        print(f"Missing model files: {[p.name for p in missing]} → downloading...")
        download_model()
        still_missing = [p for p in required if not p.exists()]
        if still_missing:
            raise FileNotFoundError(
                f"Model still incomplete after download: {[p.name for p in still_missing]}"
            )
    else:
        print("All model files present, skipping download")


def load_model():
    global recognizer
    print("Loading Vietnamese ASR model...")
    print(f"Model dir: {MODEL_DIR}")
    print(f"Files: {list(MODEL_DIR.iterdir())}")
    print(f"USE_INT8: {USE_INT8}")

    recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=str(ENCODER_PATH),
        decoder=str(DECODER_PATH),
        joiner=str(JOINER_PATH),
        tokens=str(TOKENS_PATH),
        num_threads=4,
        sample_rate=16000,
        provider="cpu",
    )
    print("Model loaded successfully!")


@app.on_event("startup")
async def startup_event():
    ensure_model()
    load_model()


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model": HF_MODEL_ID,
        "language": "Vietnamese",
        "api_type": "FastAPI",
        "endpoints": ["/health", "/transcribe"]
    }


@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    if recognizer is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        audio_data, sample_rate = sf.read(tmp_path)

        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)

        if sample_rate != 16000:
            import scipy.signal
            num_samples = int(len(audio_data) * 16000 / sample_rate)
            audio_data = scipy.signal.resample(audio_data, num_samples)

        stream = recognizer.create_stream()
        stream.accept_waveform(16000, audio_data.astype(np.float32))
        recognizer.decode_stream(stream)
        result = stream.result

        return {"text": result.text.strip(), "duration": len(audio_data) / 16000}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8090)
