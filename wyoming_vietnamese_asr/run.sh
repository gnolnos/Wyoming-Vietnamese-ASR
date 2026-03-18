#!/bin/bash
set -e

CONFIG_PATH=/data/options.json

# Read configuration
EMBEDDING_MODEL=$(jq --raw-output '.embedding_model // "qwen3-embedding:4b"' "$CONFIG_PATH")
LOG_LEVEL=$(jq --raw-output '.log_level // "info"' "$CONFIG_PATH")

# Set Rust log level
export RUST_LOG="${LOG_LEVEL}"

echo "====================================="
echo "🧠 Wyoming Vietnamese ASR Add-on"
echo "====================================="
echo "Model: Zipformer-30M-RNNT-6000h"
echo "Embedding: ${EMBEDDING_MODEL}"
echo "Log level: ${LOG_LEVEL}"
echo "====================================="

# Change to app directory
cd /app

# Start Wyoming server
exec python3 server/main.py
