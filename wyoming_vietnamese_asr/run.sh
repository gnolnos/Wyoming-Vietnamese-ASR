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

# Ensure model directory exists
mkdir -p /data/model

# Download model if not present
echo "🔽 Checking model files..."
python3 /app/download_model.py

# Change to app directory
cd /app

# Start Wyoming server
exec python3 server/main.py
