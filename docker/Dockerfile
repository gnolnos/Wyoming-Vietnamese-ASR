# ============================================================
# STAGE 1: Builder
# ============================================================
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
RUN pip install --no-cache-dir --prefix=/install "huggingface_hub[cli]"

# ============================================================
# STAGE 2: Runtime
# ============================================================
FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /install /usr/local
COPY server/ ./server/
COPY fastapi_server.py .

RUN mkdir -p /app/model \
    && useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

# ── Default ENV ──────────────────────────────────────────────
ENV MODEL_DIR="/app/model" \
    USE_INT8="false" \
    TOKENS_FILE="config.json" \
    NUM_THREADS="4" \
    PROVIDER="cpu" \
    SAMPLE_RATE="16000" \
    SERVER_HOST="0.0.0.0" \
    SERVER_PORT="10400" \
    API_HOST="0.0.0.0" \
    API_PORT="8090" \
    LOG_LEVEL="INFO" \
    HF_MODEL_ID="hynt/Zipformer-30M-RNNT-6000h" \
    HF_TOKEN="" \
    FORCE_DOWNLOAD="false" \
    MODE="wyoming"

EXPOSE 10400 8090

# ── Health check động theo MODE ──────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
    CMD python -c " \
import os, socket, urllib.request; \
mode = os.environ.get('MODE','wyoming'); \
port = int(os.environ.get('SERVER_PORT', 10400)) if mode == 'wyoming' else int(os.environ.get('API_PORT', 8090)); \
s = socket.socket(); s.settimeout(5); r = s.connect_ex(('localhost', port)); s.close(); exit(r)"

# ── CMD theo MODE ─────────────────────────────────────────────
# MODE=wyoming  → Wyoming server  [default]
# MODE=fastapi  → FastAPI server
CMD ["/bin/sh", "-c", "\
  if [ \"$MODE\" = 'fastapi' ]; then \
    exec python fastapi_server.py; \
  else \
    exec python server/main.py; \
  fi"]