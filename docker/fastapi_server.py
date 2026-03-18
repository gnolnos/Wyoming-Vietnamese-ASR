#!/usr/bin/env python3
"""
FastAPI Server for Vietnamese ASR (Zipformer-30M-RNNT)
Configurable via environment variables. Shares config with Wyoming server.
"""

import logging
import os
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
import soundfile as sf
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import PlainTextResponse

import sherpa_onnx

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _get_bool(key: str, default: bool = False) -> bool:
    return os.environ.get(key, str(default)).lower() in ("1", "true", "yes")

def _get_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default

# ─────────────────────────────────────────────
# Config từ Environment Variables
# ─────────────────────────────────────────────
MODEL_DIR    = Path(os.environ.get("MODEL_DIR", "/app/model"))
_USE_INT8    = _get_bool("USE_INT8", False)
_suffix      = ".int8.onnx" if _USE_INT8 else ".onnx"
_base        = "epoch-20-avg-10"

ENCODER_FILE = os.environ.get("ENCODER_FILE", f"encoder-{_base}{_suffix}")
DECODER_FILE = os.environ.get("DECODER_FILE", f"decoder-{_base}{_suffix}")
JOINER_FILE  = os.environ.get("JOINER_FILE",  f"joiner-{_base}{_suffix}")
TOKENS_FILE  = os.environ.get("TOKENS_FILE",  "config.json")

ENCODER_PATH = MODEL_DIR / ENCODER_FILE
DECODER_PATH = MODEL_DIR / DECODER_FILE
JOINER_PATH  = MODEL_DIR / JOINER_FILE
TOKENS_PATH  = MODEL_DIR / TOKENS_FILE

NUM_THREADS  = _get_int("NUM_THREADS", 4)
SAMPLE_RATE  = _get_int("SAMPLE_RATE", 16000)
PROVIDER     = os.environ.get("PROVIDER", "cpu")

# FastAPI server config
API_HOST     = os.environ.get("API_HOST", "0.0.0.0")
API_PORT     = _get_int("API_PORT", 8090)
LOG_LEVEL    = os.environ.get("LOG_LEVEL", "INFO").upper()

# HuggingFace download config
HF_MODEL_ID    = os.environ.get("HF_MODEL_ID", "hynt/Zipformer-30M-RNNT-6000h")
HF_TOKEN       = os.environ.get("HF_TOKEN", "") or None
FORCE_DOWNLOAD = _get_bool("FORCE_DOWNLOAD", False)

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
_LOGGER = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Metrics (Prometheus-compatible)
# ─────────────────────────────────────────────
_metrics = {
    "requests_total": 0,
    "requests_success": 0,
    "requests_error": 0,
    "total_audio_seconds": 0.0,
    "total_inference_ms": 0.0,
}

# ─────────────────────────────────────────────
# Model
# ─────────────────────────────────────────────
REQUIRED_FILES = [ENCODER_FILE, DECODER_FILE, JOINER_FILE, TOKENS_FILE]
recognizer = None


def _model_exists() -> bool:
    missing = [f for f in REQUIRED_FILES if not (MODEL_DIR / f).exists()]
    if missing:
        _LOGGER.warning(f"Missing model files: {missing}")
        return False
    return True


def download_model():
    """Download model từ HuggingFace"""
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        _LOGGER.error("huggingface_hub not installed!")
        raise

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    _LOGGER.info(f"📥 Downloading model: {HF_MODEL_ID}")

    allow_patterns = ["*.onnx", "config.json", "bpe.model"]
    ignore_patterns = ["*.int8.onnx"] if not _USE_INT8 else []

    snapshot_download(
        repo_id=HF_MODEL_ID,
        local_dir=str(MODEL_DIR),
        allow_patterns=allow_patterns,
        ignore_patterns=ignore_patterns,
        token=HF_TOKEN,
    )
    _LOGGER.info("✅ Model downloaded!")


def ensure_model():
    if FORCE_DOWNLOAD:
        _LOGGER.warning("⚠️  FORCE_DOWNLOAD=true → re-downloading")
        download_model()
        return
    if not _model_exists():
        _LOGGER.info("⚠️  Model missing → auto-downloading...")
        download_model()
    else:
        _LOGGER.info("✅ Model files exist, skipping download")


def load_model():
    global recognizer

    _LOGGER.info("=" * 55)
    _LOGGER.info("Loading Vietnamese ASR model (FastAPI)...")
    _LOGGER.info(f"  ENCODER  : {ENCODER_PATH}")
    _LOGGER.info(f"  DECODER  : {DECODER_PATH}")
    _LOGGER.info(f"  JOINER   : {JOINER_PATH}")
    _LOGGER.info(f"  TOKENS   : {TOKENS_PATH}")
    _LOGGER.info(f"  THREADS  : {NUM_THREADS} | PROVIDER: {PROVIDER}")
    _LOGGER.info(f"  USE_INT8 : {_USE_INT8}")
    _LOGGER.info("=" * 55)

    for path, label in [
        (ENCODER_PATH, "ENCODER"),
        (DECODER_PATH, "DECODER"),
        (JOINER_PATH,  "JOINER"),
        (TOKENS_PATH,  "TOKENS"),
    ]:
        if not path.exists():
            raise FileNotFoundError(f"❌ {label} not found: {path}")

    recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=str(ENCODER_PATH),
        decoder=str(DECODER_PATH),
        joiner=str(JOINER_PATH),
        tokens=str(TOKENS_PATH),
        num_threads=NUM_THREADS,
        sample_rate=SAMPLE_RATE,
        provider=PROVIDER,
        decoding_method="greedy_search",
    )
    _LOGGER.info("✅ Model loaded successfully!")


# ─────────────────────────────────────────────
# Lifespan (thay on_event deprecated)
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup & shutdown lifecycle"""
    _LOGGER.info("🚀 FastAPI ASR Server starting...")
    ensure_model()
    load_model()
    _LOGGER.info(f"✅ API ready on {API_HOST}:{API_PORT}")
    yield
    _LOGGER.info("🛑 FastAPI ASR Server shutting down...")


# ─────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────
app = FastAPI(
    title="Vietnamese ASR - Zipformer-30M-RNNT",
    version="1.0.0",
    description="Vietnamese Speech-to-Text via Zipformer-30M RNNT. WER 7.97% on VLSP2025.",
    lifespan=lifespan,
)


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model": HF_MODEL_ID,
        "variant": "int8" if _USE_INT8 else "fp32",
        "language": "vi",
        "provider": PROVIDER,
        "num_threads": NUM_THREADS,
        "api_port": API_PORT,
        "metrics": {
            "requests_total": _metrics["requests_total"],
            "requests_success": _metrics["requests_success"],
            "requests_error": _metrics["requests_error"],
            "total_audio_seconds": round(_metrics["total_audio_seconds"], 2),
            "avg_inference_ms": round(
                _metrics["total_inference_ms"] / max(_metrics["requests_success"], 1), 1
            ),
        },
    }


@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus-compatible metrics endpoint"""
    success = _metrics["requests_success"]
    avg_ms = _metrics["total_inference_ms"] / max(success, 1)

    return (
        f'# HELP asr_requests_total Total transcription requests\n'
        f'# TYPE asr_requests_total counter\n'
        f'asr_requests_total {_metrics["requests_total"]}\n'
        f'\n'
        f'# HELP asr_requests_success Successful transcriptions\n'
        f'# TYPE asr_requests_success counter\n'
        f'asr_requests_success {success}\n'
        f'\n'
        f'# HELP asr_requests_error Failed transcriptions\n'
        f'# TYPE asr_requests_error counter\n'
        f'asr_requests_error {_metrics["requests_error"]}\n'
        f'\n'
        f'# HELP asr_audio_seconds_total Total audio duration processed\n'
        f'# TYPE asr_audio_seconds_total counter\n'
        f'asr_audio_seconds_total {_metrics["total_audio_seconds"]:.3f}\n'
        f'\n'
        f'# HELP asr_inference_ms_avg Average inference latency (ms)\n'
        f'# TYPE asr_inference_ms_avg gauge\n'
        f'asr_inference_ms_avg {avg_ms:.1f}\n'
    )


@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    if recognizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    _metrics["requests_total"] += 1
    tmp_path = None

    try:
        # Save upload to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        # Read audio
        audio_data, sample_rate = sf.read(tmp_path)
        _LOGGER.info(f"Audio: {len(audio_data)} samples @ {sample_rate}Hz, shape={audio_data.shape}")

        # Mono conversion
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)

        # Resample nếu cần (dùng resample_poly — chính xác hơn resample)
        if sample_rate != SAMPLE_RATE:
            from scipy.signal import resample_poly
            import math
            gcd = math.gcd(SAMPLE_RATE, sample_rate)
            audio_data = resample_poly(
                audio_data,
                up=SAMPLE_RATE // gcd,
                down=sample_rate // gcd,
            )
            _LOGGER.info(f"Resampled: {sample_rate}Hz → {SAMPLE_RATE}Hz")

        audio_data = audio_data.astype(np.float32)
        duration = len(audio_data) / SAMPLE_RATE

        # Inference
        t_start = time.perf_counter()
        stream = recognizer.create_stream()
        stream.accept_waveform(SAMPLE_RATE, audio_data)
        recognizer.decode_stream(stream)
        inference_ms = (time.perf_counter() - t_start) * 1000

        text = stream.result.text.strip()
        rtf = inference_ms / 1000 / max(duration, 0.001)  # Real-Time Factor

        _LOGGER.info(
            f"Transcription: '{text}' | "
            f"duration={duration:.2f}s | "
            f"inference={inference_ms:.1f}ms | "
            f"RTF={rtf:.3f}"
        )

        # Update metrics
        _metrics["requests_success"] += 1
        _metrics["total_audio_seconds"] += duration
        _metrics["total_inference_ms"] += inference_ms

        return {
            "text": text,
            "duration": round(duration, 3),
            "inference_ms": round(inference_ms, 1),
            "rtf": round(rtf, 4),
        }

    except Exception as e:
        _metrics["requests_error"] += 1
        _LOGGER.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level=LOG_LEVEL.lower(),
    )
