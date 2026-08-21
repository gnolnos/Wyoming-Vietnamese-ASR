#!/bin/bash
set -e

CONFIG_PATH=/data/options.json

# Read configuration
LOG_LEVEL=$(jq --raw-output '.log_level // "info"' "$CONFIG_PATH")
EXTERNAL_MODEL_PATH=$(jq --raw-output '.external_model_path // "/data/model"' "$CONFIG_PATH")
USE_INT8=$(jq --raw-output '.use_int8 // "false"' "$CONFIG_PATH")

# Set log level
export RUST_LOG="${LOG_LEVEL}"
export LOG_LEVEL="${LOG_LEVEL}"

# Set model path (default: /data/model)
export MODEL_PATH="${EXTERNAL_MODEL_PATH}"

# Optional INT8 variant (smaller, faster on CPU, slight accuracy trade-off)
export USE_INT8="${USE_INT8}"

echo "====================================="
echo "🧠 Wyoming Vietnamese ASR Add-on"
echo "====================================="
echo "Model: hynt/Zipformer-30M-RNNT-6000h"
echo "Log level: ${LOG_LEVEL}"
echo "Model path: ${MODEL_PATH}"
echo "USE_INT8: ${USE_INT8}"
echo "====================================="

# Install system dependencies (Alpine) - idempotent
echo "📦 Ensuring system dependencies..."
apk add --no-cache python3 py3-pip bash jq ffmpeg libsndfile || true

# Install Python packages (first run only)
echo "🔧 Installing Python packages..."
pip3 install --no-cache-dir --break-system-packages \
    wyoming==1.4.0 \
    soundfile==0.12.1 \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    sherpa-onnx \
    onnxruntime==1.16.3 \
    huggingface-hub==0.20.3

# Ensure model directory exists
mkdir -p "${MODEL_PATH}"

# Download model if not present
echo "🔽 Checking model files in ${MODEL_PATH}..."
python3 /app/download_model.py

# Change to app directory
cd /app

# Start Wyoming server
echo "🚀 Starting server..."
exec python3 server/main.py
