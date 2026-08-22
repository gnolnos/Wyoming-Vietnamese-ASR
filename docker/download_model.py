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

Update check: each run compares the HF repo's current commit SHA
(model_info().sha) against the SHA saved at .hf_revision the last time we
downloaded. If they differ => a newer model version exists => re-download.
Always safe: a network error on the check just warns and keeps the local
model (never crashes the container / never deletes existing files).
"""

import os
import sys
from pathlib import Path

try:
    from huggingface_hub import snapshot_download, HfApi
except ImportError:
    print("ERROR: huggingface_hub not installed. Please install it via apk/pip.", file=sys.stderr)
    sys.exit(1)

REPO_ID = os.getenv("HF_MODEL_ID", "hynt/Zipformer-30M-RNNT-6000h")
# NOTE: standalone docker dùng /app/model; add-on HA dùng /data/model (set qua run.sh).
MODEL_DIR = Path(os.getenv("MODEL_PATH", "/app/model"))
FORCE = os.getenv("FORCE_DOWNLOAD", "false").lower() in ("1", "true", "yes")
USE_INT8 = os.getenv("USE_INT8", "false").lower() in ("1", "true", "yes")
# Bật/tắt kiểm tra model mới. Mặc định TRUE: tự check & cập nhật mỗi lần chạy.
# Tắt bằng CHECK_UPDATE=false nếu muốn khóa version đã có (không đụng mạng).
CHECK_UPDATE = os.getenv("CHECK_UPDATE", "true").lower() in ("1", "true", "yes")

REVISION_FILE = MODEL_DIR / ".hf_revision"


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


def _remote_revision() -> str | None:
    """Return the HF repo's current root commit SHA, or None if unreachable."""
    try:
        info = HfApi().model_info(REPO_ID, files_metadata=False)
        return info.sha
    except Exception as e:  # network / auth / rate-limit — never hard-fail
        print(f"⚠️  Cannot reach Hub to check for model updates: {e}", file=sys.stderr)
        return None


def _saved_revision() -> str:
    if REVISION_FILE.exists():
        return REVISION_FILE.read_text().strip()
    return ""


def _save_revision(sha: str) -> None:
    try:
        REVISION_FILE.write_text(sha)
    except Exception as e:
        print(f"⚠️  Could not save revision marker: {e}", file=sys.stderr)


def _download(remote_sha: str | None) -> bool:
    """Download model files; return True on success. `remote_sha` marks revision."""
    # Select only the files that actually exist in the HF repo.
    # FP32: *.onnx + config.json + bpe.model, exclude int8 variants.
    # INT8: *.int8.onnx + config.json + bpe.model.
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
        return False

    if not _model_complete():
        print("❌ Model download completed but required files are missing.", file=sys.stderr)
        return False

    # Update the version marker AFTER a successful download so a failed/partial
    # download never looks "up to date" on the next run.
    if remote_sha:
        _save_revision(remote_sha)
    return True


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🔽 Model repo : {REPO_ID}")
    print(f"🔽 Target dir : {MODEL_DIR}")
    print(f"🔽 USE_INT8   : {USE_INT8}")
    print(f"🔽 CHECK_UPDATE: {CHECK_UPDATE}")

    complete = _model_complete()

    if complete and not FORCE:
        if not CHECK_UPDATE:
            print("✓ Model up to date (CHECK_UPDATE=false). Skipping network check + download.")
            return
        remote = _remote_revision()
        if remote is None:
            # Can't reach the Hub — keep the working local model, don't re-touch.
            print("✓ Local model kept (cannot verify updates offline).")
            return
        saved = _saved_revision()
        if saved == "":
            # First run of this feature: record current revision, don't re-download.
            _save_revision(remote)
            print(f"✓ Model present. Recorded revision {remote[:12]} (no re-download).")
            return
        if remote == saved:
            print(f"✓ Model is up to date (revision {remote[:12]}).")
            return
        # remote != saved  →  a newer version exists
        print(f"🆕 New model revision {remote[:12]} (local {saved[:12]}) — downloading update...")
        if _download(remote):
            print(f"🎉 Model updated to revision {remote[:12]}!")
        else:
            sys.exit(1)
        return

    if FORCE:
        print("⚠️  FORCE_DOWNLOAD=true — re-downloading model files.")

    remote = _remote_revision() if CHECK_UPDATE else None
    print("🔽 Downloading model files...")
    if _download(remote):
        print("🎉 Model download complete!")
        print(f"📂 Files: {sorted(p.name for p in MODEL_DIR.iterdir() if not p.name.startswith('.'))}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()