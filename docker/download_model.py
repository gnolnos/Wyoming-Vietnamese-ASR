#!/usr/bin/env python3
"""
Download Vietnamese ASR model from HuggingFace.

Files needed (per repo hynt/Zipformer-30M-RNNT-6000h):
- encoder-epoch-20-avg-10.onnx      (or .int8.onnx when USE_INT8=true)
- decoder-epoch-20-avg-10.onnx      (or .int8.onnx)
- joiner-epoch-20-avg-10.onnx       (or .int8.onnx)
- config.json                       → BPE token vocab (NOT a JSON config!)
- bpe.model

NOTE: The repo does NOT contain "tokens.txt". The BPE vocabulary ships as
`config.json` in k2-fsa / csukuangfj style transducer repos, so we must
download `config.json`, never `tokens.txt`. Idempotent: skips files that
already exist unless FORCE_DOWNLOAD=true.
"""

import os
import sys
from pathlib import Path

try:
    from huggingface_hub import snapshot_download
except ImportError:
    print("ERROR: huggingface_hub not installed. Please install it via apk/pip.", file=sys.stderr)
    sys.exit(1)

REPO_ID = os.getenv("HF_MODEL_ID", "hynt/Zipformer-30M-RNNT-6000h")
# NOTE: standalone docker dùng /app/model; add-on HA dùng /data/model (set qua run.sh).
MODEL_DIR = Path(os.getenv("MODEL_PATH", "/app/model"))
FORCE = os.getenv("FORCE_DOWNLOAD", "false").lower() in ("1", "true", "yes")
USE_INT8 = os.getenv("USE_INT8", "false").lower() in ("1", "true", "yes")


def _model_complete() -> bool:
    """Return True when every required model file is present."""
    suffix = ".int8.onnx" if USE_INT8 else ".onnx"
    required = [
        f"encoder-epoch-20-avg-10{suffix}",
        f"decoder-epoch-20-avg-10{suffix}",
        f"joiner-epoch-20-avg-10{suffix}",
        "config.json",
        "bpe.model",
    ]
    missing = [f for f in required if not (MODEL_DIR / f).exists()]
    return not missing


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🔽 Model repo : {REPO_ID}")
    print(f"🔽 Target dir : {MODEL_DIR}")
    print(f"🔽 USE_INT8   : {USE_INT8}")

    if _model_complete() and not FORCE:
        print("✓ All model files already present — skipping download.")
        return

    if FORCE:
        print("⚠️  FORCE_DOWNLOAD=true — re-downloading model files.")

    # Select only the files that actually exist in the HF repo.
    # FP32 build: fetch *.onnx + config.json + bpe.model, exclude int8 variants.
    # INT8 build: fetch *.int8.onnx + config.json + bpe.model.
    if USE_INT8:
        allow = ["*.int8.onnx", "config.json", "bpe.model"]
        ignore = []
    else:
        allow = ["*.onnx", "config.json", "bpe.model"]
        ignore = ["*.int8.onnx"]

    try:
        snapshot_download(
            repo_id=REPO_ID,
            local_dir=str(MODEL_DIR),
            allow_patterns=allow,
            ignore_patterns=ignore,
        )
    except Exception as e:
        print(f"❌ Model download failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not _model_complete():
        print("❌ Model download completed but required files are missing.", file=sys.stderr)
        sys.exit(1)

    print("🎉 Model download complete!")
    print(f"📂 Files: {sorted(p.name for p in MODEL_DIR.iterdir() if not p.name.startswith('.'))}")


if __name__ == "__main__":
    main()
