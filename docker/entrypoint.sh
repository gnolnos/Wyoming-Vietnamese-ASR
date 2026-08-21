#!/bin/sh
# ============================================================
#  Wyoming Vietnamese ASR - Entrypoint
# ============================================================
#  Tự tải model từ HuggingFace khi chưa có (docker pull → run tự
#  hoạt động, không cần user tự tải model thủ công).
#
#  Flow:
#    1. Nếu model chưa đầy đủ → chạy download_model (tải đúng file).
#    2. Start server theo MODE (wyoming | fastapi).
#    3. Thoát có lỗi nếu không có model → để tránh crash loop âm thầm.
set -e

MODEL_DIR="${MODEL_DIR:-/app/model}"
# download_model.py đọc MODEL_PATH; server đọc MODEL_DIR. Đồng bộ cả hai.
export MODEL_PATH="${MODEL_DIR}"
export MODEL_DIR="${MODEL_DIR}"
MODE="${MODE:-wyoming}"

echo "====================================="
echo "  Wyoming Vietnamese ASR"
echo "  Model dir : ${MODEL_DIR}"
echo "  MODE      : ${MODE}"
echo "====================================="

# Tạo thư mục model + đảm bảo appuser có thể ghi khi KHÔNG dùng user:root
mkdir -p "${MODEL_DIR}"
if [ "$(id -u)" = "0" ]; then
    chown -R appuser:appuser "${MODEL_DIR}" 2>/dev/null || true
fi

# Kiểm tra model đầy đủ chưa; nếu thiếu thì tải.
if [ -n "$(ls -A "${MODEL_DIR}" 2>/dev/null)" ]; then
    echo "📁 Model dir có sẵn, kiểm tra file cần thiết..."
fi

python3 /app/download_model.py

# Start server theo mode
cd /app
if [ "${MODE}" = "fastapi" ]; then
    echo "🚀 Starting FastAPI server (port ${API_PORT:-8090})..."
    exec python3 fastapi_server.py
else
    echo "🚀 Starting Wyoming server (port ${SERVER_PORT:-10400})..."
    exec python3 server/main.py
fi