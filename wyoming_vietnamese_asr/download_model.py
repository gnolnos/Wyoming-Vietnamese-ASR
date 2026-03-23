#!/usr/bin/env python3
"""
Download Vietnamese ASR model from HuggingFace.
Files needed:
- encoder-epoch-20-avg-10.onnx
- decoder-epoch-20-avg-10.onnx
- joiner-epoch-20-avg-10.onnx
- tokens.txt
- bpe.model
"""

import os
import sys
from pathlib import Path

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    print("ERROR: huggingface_hub not installed. Please install it via apk/pip.", file=sys.stderr)
    sys.exit(1)

REPO_ID = "hynt/Zipformer-30M-RNNT-6000h"
MODEL_DIR = Path(os.getenv("MODEL_PATH", "/data/model"))
MODEL_DIR.mkdir(parents=True, exist_ok=True)

FILES = [
    "encoder-epoch-20-avg-10.onnx",
    "decoder-epoch-20-avg-10.onnx",
    "joiner-epoch-20-avg-10.onnx",
    "tokens.txt",
    "bpe.model",
]

def main():
    print(f"🔽 Downloading model from {REPO_ID} to {MODEL_DIR}...")
    for filename in FILES:
        dest = MODEL_DIR / filename
        if dest.exists():
            print(f"✓ {filename} already exists, skipping.")
            continue
        print(f"Downloading {filename}...")
        try:
            hf_hub_download(
                repo_id=REPO_ID,
                filename=filename,
                local_dir=MODEL_DIR,
                local_dir_use_symlinks=False,
            )
            print(f"✅ {filename} downloaded.")
        except Exception as e:
            print(f"❌ Failed to download {filename}: {e}", file=sys.stderr)
            sys.exit(1)
    print("🎉 Model download complete!")

if __name__ == "__main__":
    main()
