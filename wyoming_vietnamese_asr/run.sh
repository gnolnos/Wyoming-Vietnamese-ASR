#!/bin/bash
set -e

CONFIG_PATH=/data/options.json

# Read configuration
LOG_LEVEL=$(jq --raw-output '.log_level // "info"' "$CONFIG_PATH")

# Set log level
export RUST_LOG="${LOG_LEVEL}"
export LOG_LEVEL="${LOG_LEVEL}"

echo "====================================="
echo "🧠 Wyoming Vietnamese ASR Add-on"
echo "====================================="
echo "Model: hynt/Zipformer-30M-RNNT-6000h"
echo "Log level: ${LOG_LEVEL}"
echo "====================================="

# Install system dependencies (Alpine) - idempotent
echo "📦 Ensuring system dependencies..."
apk add --no-cache python3 py3-pip bash jq ffmpeg libsndfile || true

# Install Python packages (first run only - cached in layer if we rebuild, but here we do it at runtime)
echo "🔧 Installing Python packages..."
pip3 install --no-cache-dir --break-system-packages \
    wyoming==1.4.0 \
    soundfile==0.12.1 \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    onnxruntime==1.16.3 \
    huggingface-hub==0.20.3

# Ensure model directory exists
mkdir -p /data/model

# Download model if not present
echo "🔽 Checking/downloading model..."
python3 /app/download_model.py

# Change to app directory
cd /app

# Start Wyoming server
echo "🚀 Starting server..."
exec python3 server/main.py
