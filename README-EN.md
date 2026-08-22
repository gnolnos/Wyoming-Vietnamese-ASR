# Wyoming Vietnamese ASR for Home Assistant

[![GitHub Release](https://img.shields.io/github/v/release/gnolnos/wyoming-vietnamese-asr)](https://github.com/gnolnos/wyoming-vietnamese-asr/releases)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz/)
[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fgnolnos%2FWyoming-Vietnamese-ASR)
[![Docker](https://img.shields.io/docker/pulls/gnolnos/wyoming-vietnamese-asr)](https://hub.docker.com/r/gnolnos/wyoming-vietnamese-asr)

**Vietnamese Automatic Speech Recognition (ASR) integration for Home Assistant.**

**[Tiếng Việt](README.md)** | English

---

### 🏠 Add to Home Assistant (Add-on Repository)

Add this repository to Home Assistant:

1. Mở **HACS** → **Integrations**
2. Click **⋮** (menu góc phải) → **Custom repositories**
3. Nhập:
   - **Repository:** `https://github.com/gnolnos/Wyoming-Vietnamese-ASR`
   - **Category:** `Integration`
4. Click **Add**
5. Tìm **Wyoming Vietnamese ASR** → **Download**
6. **Khởi động lại** Home Assistant
7. Thêm integration qua **Settings → Devices & Services**

---

## 🎯 Tính năng chính

- 🇻🇳 **Nhận dạng tiếng Việt chính xác**: WER 7.97% (độ lỗi nhận dạng chỉ 7.97%)
- 🏠 **Tích hợp native với Home Assistant**: Sử dụng Wyoming protocol
- ⚡ **Độ trễ thấp**: Xử lý real-time trên CPU hoặc GPU
- 🐳 **Docker support**: Chạy standalone bên ngoài Home Assistant
- 🔧 **Dễ cấu hình**: UI configuration qua Home Assistant
- 🤖 **Tự tải model**: Lần đầu chạy tự kéo model ~200MB từ HuggingFace, không cần thao tác tay
- 🔄 **Tự check & cập nhật model**: Mỗi lần khởi động tự dò version model mới (theo commit SHA của repo HF) và tự tải bản mới nếu có. Tắt bằng `CHECK_UPDATE=false`

## 📊 Thông tin Model

| Thuộc tính | Giá trị |
|------------|---------|
| **Model** | Zipformer-30M-RNNT-6000h |
| **Ngôn ngữ** | Tiếng Việt |
| **WER** | 7.97% (VLSP2025 benchmark) |
| **Provider** | [hynt/Zipformer-30M-RNNT-6000h](https://huggingface.co/hynt/Zipformer-30M-RNNT-6000h) |
| **Kích thước** | ~30MB |
| **Thread** | 4 threads khuyến nghị |

## 🛠️ Cài đặt

### Cách 1: HACS (Khuyên dùng)

1. Mở **HACS** trong Home Assistant
2. Tìm kiếm **"Wyoming Vietnamese ASR"**
3. Click **Cài đặt**
4. **Khởi động lại** Home Assistant
5. Thêm integration qua UI

### Cách 2: Cài thủ công

1. Tải **wyoming_vietnamese.zip** từ [GitHub Releases](https://github.com/gnolnos/wyoming-vietnamese-asr/releases)
2. Giải nén vào `custom_components/wyoming_vietnamese/`
3. **Khởi động lại** Home Assistant
4. Thêm integration qua UI

### Cách 3: Docker (Standalone)

```bash
# Clone repository
git clone https://github.com/gnolnos/wyoming-vietnamese-asr.git
cd wyoming-vietnamese-asr

# Chọn 1 trong 3 template compose và chạy:
docker compose up -d                       # cả Wyoming :10400 + FastAPI :8090
# docker compose -f compose.wyoming.yaml up -d   # chỉ Wyoming
# docker compose -f compose.fastapi.yaml up -d   # chỉ FastAPI

# Kiểm tra
curl http://localhost:8090/health          # → {"status":"ok"}
docker logs wyoming-asr                    # xem auto-download model + check revision
```

- Model **tự động tải lần đầu** (~200MB) vào `./model` (bind mount) — không cần làm gì.
- Image: GHCR public `ghcr.io/gnolnos/wyoming-vietnamese-asr:v1.3.0` (tương đương Docker Hub `gnolnos/wyoming-vietnamese-asr:v1.3.0`).

## ⚙️ Cấu hình

### Cấu hình qua Home Assistant UI

1. Vào **Cài đặt** → **Thiết bị & Dịch vụ**
2. Click **+ Thêm tích hợp**
3. Tìm **"Wyoming Vietnamese ASR"**
4. Điền thông tin:
   - **Host**: Địa chỉ IP server Wyoming (mặc định: `192.168.100.150`)
   - **Port**: Cổng Wyoming server (mặc định: `10400`)
   - **Tên**: Tên tích hợp (tùy chọn)
5. Click **Hoàn tất**

### Cấu hình Docker standalone

Dùng một trong các file compose ở root repo (image GHCR public, tự tải model):

- `compose.yaml` — Wyoming :10400 **+** FastAPI :8090 (mặc định, cần cả 2)
- `compose.wyoming.yaml` — chỉ Wyoming :10400
- `compose.fastapi.yaml` — chỉ FastAPI :8090

```bash
docker compose up -d                 # hoặc docker compose -f compose.<variant>.yaml up -d
```

Network dùng **bridge + publish port** (không `network_mode: host`) nên chạy được trên mọi nền tảng (Docker Desktop/Mac/WSL). HA nối tới `wyoming-asr:10400`. Model tự tải vào `./model` (bind mount cần quyền ghi — `user: root` được giữ cho việc này).

## 🎤 Sử dụng

### Trong Home Assistant

Sau khi cài đặt, tích hợp sẽ xuất hiện như một nhà cung cấp STT:

1. Vào **Cài đặt** → **Trợ lý giọng nói**
2. Chọn trợ lý của bạn
3. Chọn **"Vietnamese ASR"** làm engine **Speech-to-Text**
4. Bắt đầu nói tiếng Việt!

### API REST (cho Xiaozzi và tích hợp ngoài)

```bash
# Gửi file audio để nhận dạng
curl -X POST "http://localhost:8090/transcribe" \
  -H "Content-Type: audio/wav" \
  --data-binary @audio.wav

# Response
{
  "text": "Xin chào thế giới",
  "duration": 2.5
}
```

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────┐
│  Home Assistant (Trợ lý giọng nói)     │
│  Wyoming STT Integration                │
└─────────────────┬───────────────────────┘
                  │ Wyoming Protocol (TCP)
                  ▼
┌─────────────────────────────────────────┐
│  Wyoming Vietnamese ASR Server          │
│  Cổng: 10400                            │
│  Model: Zipformer-30M-RNNT-6000h       │
│  CPU: 4 threads                         │
└─────────────────┬───────────────────────┘
                  │ (tùy chọn)
                  ▼
┌─────────────────────────────────────────┐
│  FastAPI Server                         │
│  Cổng: 8090 (cho Xiaozzi, REST API)    │
└─────────────────────────────────────────┘
```

## 🐳 Docker Deployment

Repo có sẵn **3 template compose** ở root (image GHCR public, tự tải model):

### Cả Wyoming + FastAPI (mặc định) — `compose.yaml`

```bash
cd wyoming-vietnamese-asr
docker compose up -d

# Kiểm tra trạng thái
docker compose ps
docker inspect wyoming-asr --format '{{.State.Health.Status}}'   # → healthy

# Xem log (auto-download model, check revision)
docker compose logs -f
```

### Chỉ Wyoming — `compose.wyoming.yaml`

```bash
docker compose -f compose.wyoming.yaml up -d   # port 10400 cho HA
```

### Chỉ FastAPI — `compose.fastapi.yaml`

```bash
docker compose -f compose.fastapi.yaml up -d   # port 8090 /transcribe cho script
```

Tất cả dùng **bridge + publish port** (không `network_mode: host`), `user: root` để ghi bind mount `./model`, và healthcheck rõ ràng trên mỗi service.

## 🔧 Xử lý sự cố

### Kết nối thất bại

**Triệu chứng:** `Connection refused` hoặc `Timeout`

**Giải pháp:**
```bash
# Kiểm tra Wyoming server đang chạy
docker ps | grep wyoming

# Kiểm tra cổng
netstat -tlnp | grep 10400

# Test kết nối
nc -zv 192.168.100.150 10400
```

### Chất lượng nhận dạng kém

**Triệu chứng:** Kết quả sai nhiều, nhận dạng không chính xác

**Giải pháp:**
1. Đảm bảo audio rõ tiếng Việt, ít tạp âm
2. Kiểm tra cài đặt microphone trong Home Assistant
3. Xác nhận model được load đúng

### Hiệu suất chậm

**Triệu chứng:** Độ trễ cao, timeout thường xuyên

**Giải pháp:**
1. Bật GPU acceleration (NVIDIA)
2. Tăng bộ nhớ (khuyến nghị 2GB+)
3. Sử dụng SSD cho file model

## 📈 Benchmark

| Mô hình | WER (%) | Kích thước | Tốc độ |
|---------|---------|------------|--------|
| **Zipformer-30M-RNNT-6000h** | **7.97** | 30MB | 0.5x real-time |
| Whisper Base | 12.5 | 74MB | 1x real-time |
| Whisper Small | 8.2 | 244MB | 2x real-time |

*Test trên CPU Intel i5-7500T, 4 threads*

## 🔗 Liên kết

- **Repository**: [github.com/gnolnos/Wyoming-Vietnamese-ASR](https://github.com/gnolnos/Wyoming-Vietnamese-ASR)
- **Docker Hub**: [hub.docker.com/r/gnolnos/wyoming-vietnamese-asr](https://hub.docker.com/r/gnolnos/wyoming-vietnamese-asr)
- **Model**: [huggingface.co/hynt/Zipformer-30M-RNNT-6000h](https://huggingface.co/hynt/Zipformer-30M-RNNT-6000h)
- **Home Assistant**: [home-assistant.io/integrations/wyoming](https://www.home-assistant.io/integrations/wyoming/)

## 🤝 Đóng góp

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/ten-tinh-nang`)
3. Commit thay đổi (`git commit -m 'Thêm tính năng XYZ'`)
4. Push lên GitHub (`git push origin feature/ten-tinh-nang`)
5. Tạo Pull Request

## 📄 Giấy phép

**MIT License** - Xem [LICENSE](LICENSE) để biết chi tiết.

## 👨‍💻 Tác giả

**gnolnos** - [github.com/gnolnos](https://github.com/gnolnos)

---

**⭐ Nếu dự án hữu ích, hãy star repository để ủng hộ!**
