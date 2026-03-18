#!/usr/bin/env python3
"""
Wyoming Protocol Server for Vietnamese ASR (Zipformer-30M-RNNT)
Configurable via environment variables. Auto-downloads model from HuggingFace.
"""

import asyncio
import logging
import os
from pathlib import Path

import numpy as np
import sherpa_onnx
from wyoming.audio import AudioStart, AudioChunk, AudioStop
from wyoming.event import Event
from wyoming.info import Describe, Info, Attribution, AsrProgram, AsrModel
from wyoming.server import AsyncEventHandler, AsyncServer
from wyoming.asr import Transcribe, Transcript
# Thêm vào đầu ensure_model() trong cả main.py và fastapi_server.py
import fcntl

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
SERVER_HOST  = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT  = _get_int("SERVER_PORT", 10400)
LOG_LEVEL    = os.environ.get("LOG_LEVEL", "INFO").upper()

# HuggingFace download config
HF_MODEL_ID      = os.environ.get("HF_MODEL_ID", "hynt/Zipformer-30M-RNNT-6000h")
HF_TOKEN         = os.environ.get("HF_TOKEN", "") or None
FORCE_DOWNLOAD   = _get_bool("FORCE_DOWNLOAD", False)

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
_LOGGER = logging.getLogger(__name__)

recognizer = None


# ─────────────────────────────────────────────
# Auto-Download Model
# ─────────────────────────────────────────────
REQUIRED_FILES = [ENCODER_FILE, DECODER_FILE, JOINER_FILE, TOKENS_FILE]

def _model_exists() -> bool:
    """Kiểm tra tất cả required files đã tồn tại chưa"""
    missing = [f for f in REQUIRED_FILES if not (MODEL_DIR / f).exists()]
    if missing:
        _LOGGER.warning(f"Missing model files: {missing}")
        return False
    return True


def download_model():
    """Download model từ HuggingFace nếu chưa có"""
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        _LOGGER.error("huggingface_hub not installed! Run: pip install huggingface_hub")
        raise

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    _LOGGER.info(f"📥 Downloading model from HuggingFace: {HF_MODEL_ID}")
    _LOGGER.info(f"   Target dir : {MODEL_DIR}")
    _LOGGER.info(f"   USE_INT8   : {_USE_INT8}")

    # Chọn pattern phù hợp với INT8 hay FP32
    if _USE_INT8:
        allow_patterns = ["*.int8.onnx", "config.json", "bpe.model"]
    else:
        # Chỉ lấy FP32 (loại bỏ int8)
        allow_patterns = ["*.onnx", "config.json", "bpe.model"]

    snapshot_download(
        repo_id=HF_MODEL_ID,
        local_dir=str(MODEL_DIR),
        allow_patterns=allow_patterns,
        ignore_patterns=["*.int8.onnx"] if not _USE_INT8 else [],
        token=HF_TOKEN,
    )

    _LOGGER.info("✅ Model downloaded successfully!")
    _LOGGER.info(f"📂 Files: {[f.name for f in MODEL_DIR.iterdir()]}")


def ensure_model():
    lock_file = MODEL_DIR / ".download.lock"
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(lock_file, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)   # Block cho đến khi có lock
        try:
            if FORCE_DOWNLOAD:
                download_model()
            elif not _model_exists():
                download_model()
            else:
                _LOGGER.info("✅ Model exists, skipping download")
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)

# ─────────────────────────────────────────────
# Model Loader
# ─────────────────────────────────────────────
def load_model():
    """Load Zipformer ONNX model vào memory"""
    global recognizer

    _LOGGER.info("=" * 55)
    _LOGGER.info("Loading Vietnamese ASR model...")
    _LOGGER.info(f"  ENCODER  : {ENCODER_PATH}")
    _LOGGER.info(f"  DECODER  : {DECODER_PATH}")
    _LOGGER.info(f"  JOINER   : {JOINER_PATH}")
    _LOGGER.info(f"  TOKENS   : {TOKENS_PATH}")
    _LOGGER.info(f"  THREADS  : {NUM_THREADS} | PROVIDER: {PROVIDER}")
    _LOGGER.info("=" * 55)

    # Validate
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
    )
    _LOGGER.info("✅ Model loaded successfully!")


# ─────────────────────────────────────────────
# Wyoming Event Handler
# ─────────────────────────────────────────────
class VietnameseASREventHandler(AsyncEventHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.audio_buffer = bytearray()
        self.sample_rate  = SAMPLE_RATE
        self.channels     = 1

    def _transcribe(self) -> str:
        audio_data = (
            np.frombuffer(self.audio_buffer, dtype=np.int16)
            .astype(np.float32) / 32768.0
        )
        if self.channels > 1:
            audio_data = audio_data.reshape(-1, self.channels).mean(axis=1)

        stream = recognizer.create_stream()
        stream.accept_waveform(self.sample_rate, audio_data)
        recognizer.decode_stream(stream)
        return stream.result.text.strip()

    async def handle_event(self, event: Event) -> bool:

        if Describe.is_type(event.type):
            _LOGGER.info("Handling Describe event")
            info = Info(
                asr=[AsrProgram(
                    name="vietnamese_asr",
                    attribution=Attribution(
                        name="hynt",
                        url=f"https://huggingface.co/{HF_MODEL_ID}",
                    ),
                    installed=True,
                    description="Vietnamese ASR (Zipformer-30M-RNNT-6000h)",
                    models=[AsrModel(
                        name="zipformer-vietnamese-30m",
                        attribution=Attribution(
                            name="hynt",
                            url=f"https://huggingface.co/{HF_MODEL_ID}",
                        ),
                        installed=True,
                        description="Zipformer-30M-RNNT-6000h - WER 7.97% on VLSP2025",
                        languages=["vi"],
                    )],
                )],
            )
            await self.write_event(info.event())
            return True

        if AudioStart.is_type(event.type):
            audio_start       = AudioStart.from_event(event)
            self.sample_rate  = audio_start.rate
            self.channels     = audio_start.channels
            self.audio_buffer = bytearray()
            _LOGGER.info(f"Audio started: rate={self.sample_rate}, ch={self.channels}")
            return True

        if AudioChunk.is_type(event.type):
            chunk = AudioChunk.from_event(event)
            self.audio_buffer.extend(chunk.audio)
            _LOGGER.debug(f"Chunk: {len(chunk.audio)} bytes")
            return True

        if AudioStop.is_type(event.type):
            _LOGGER.info(f"Audio stopped, buffer: {len(self.audio_buffer)} bytes")
            if not self.audio_buffer:
                _LOGGER.warning("Empty audio buffer")
                await self.write_event(Transcript(text="").event())
                return True
            try:
                text = self._transcribe()
                _LOGGER.info(f"Transcription: '{text}'")
                await self.write_event(Transcript(text=text).event())
            except Exception as e:
                _LOGGER.error(f"Transcription error: {e}", exc_info=True)
                await self.write_event(Transcript(text="").event())
            finally:
                self.audio_buffer = bytearray()
            return True

        if Transcribe.is_type(event.type):
            _LOGGER.info("Transcribe event received")
            if self.audio_buffer:
                try:
                    text = self._transcribe()
                    _LOGGER.info(f"Transcription: '{text}'")
                    await self.write_event(Transcript(text=text).event())
                except Exception as e:
                    _LOGGER.error(f"Transcription error: {e}", exc_info=True)
                    await self.write_event(Transcript(text="").event())
                finally:
                    self.audio_buffer = bytearray()
            return True

        _LOGGER.debug(f"Unhandled event: {event.type}")
        return True


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────
def handler_factory(reader, writer):
    return VietnameseASREventHandler(reader, writer)


async def main():
    _LOGGER.info("🚀 Starting Wyoming Vietnamese ASR Server")

    # Step 1: Ensure model exists (download if needed)
    ensure_model()

    # Step 2: Load model into memory
    load_model()

    # Step 3: Start Wyoming server
    uri = f"tcp://{SERVER_HOST}:{SERVER_PORT}"
    server = AsyncServer.from_uri(uri)
    _LOGGER.info(f"✅ Wyoming server listening on {uri}")

    await server.run(handler_factory)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _LOGGER.info("Server stopped by user")
    except Exception as e:
        _LOGGER.error(f"Server error: {e}", exc_info=True)
        raise
