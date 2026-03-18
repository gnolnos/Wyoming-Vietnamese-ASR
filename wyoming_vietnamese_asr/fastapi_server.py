#!/usr/bin/env python3
"""
FastAPI Server for Vietnamese ASR (Zipformer-30M-RNNT)
Provides REST API endpoint for Xiaozhi STT integration
"""

import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException

import sherpa_onnx

app = FastAPI(title="Vietnamese ASR - Zipformer-30M-RNNT", version="1.0.0")

MODEL_DIR = Path("/app/model")
ENCODER_PATH = MODEL_DIR / "encoder-epoch-20-avg-10.onnx"
DECODER_PATH = MODEL_DIR / "decoder-epoch-20-avg-10.onnx"
JOINER_PATH = MODEL_DIR / "joiner-epoch-20-avg-10.onnx"
TOKENS_PATH = MODEL_DIR / "tokens.txt"

recognizer = None


def load_model():
    global recognizer
    print("Loading Vietnamese ASR model...")
    print(f"Model dir: {MODEL_DIR}")
    print(f"Files: {list(MODEL_DIR.iterdir())}")
    
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
    load_model()


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model": "Zipformer-30M-RNNT-6000h",
        "language": "Vietnamese",
        "api_type": "FastAPI",
        "endpoints": ["/health", "/transcribe"]
    }


@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    if recognizer is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
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
        
        Path(tmp_path).unlink(missing_ok=True)
        
        return {"text": result.text.strip(), "duration": len(audio_data) / 16000}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8090)
