# Wyoming Vietnamese ASR cho Home Assistant

[![GitHub Release](https://img.shields.io/github/v/release/gnolnos/wyoming-vietnamese-asr)](https://github.com/gnolnos/wyoming-vietnamese-asr/releases)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz/)
[![Docker](https://img.shields.io/docker/pulls/gnolnos/wyoming-vietnamese-asr)](https://hub.docker.com/r/gnolnos/wyoming-vietnamese-asr)

**Tích hợp nhận dạng giọng nói tiếng Việt (ASR) cho Home Assistant sử dụng Wyoming protocol.**

## 🎯 Tính năng chính

- 🇻🇳 **Nhận dạng tiếng Việt chính xác**: WER 7.97% (độ lỗi nhận dạng chỉ 7.97%)
- 🏠 **Tích hợp native với Home Assistant**: Sử dụng Wyoming protocol
- ⚡ **Độ trễ thấp**: Xử lý real-time trên CPU hoặc GPU
- 🐳 **Docker support**: Chạy standalone bên ngoài Home Assistant
- 🔧 **Dễ cấu hình**: UI configuration qua Home Assistant

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
cd wyoming-vietnamese-asr/docker

# Tạo thư mục model và tải model
mkdir model
# Tải model từ HuggingFace và đặt vào thư mục model

# Khởi động dịch vụ
docker compose up -d
```

## ⚙️ Cấu hình

### Cấu hình qua Home Assistant UI

1. Vào **Cài đặt** → **Thiết bị & Dịch vụ**
2. Click **+ Thêm tích hợp**
3. Tìm **"Wyoming Vietnamese ASR"**
4. Điền thông tin:
   - **Host**: Địa chỉ IP server Wyoming (mặc định: `192.168.100.150`)
   - **Port**: Cổng Wyoming server (mặc định: `10301`)
   - **Tên**: Tên tích hợp (tùy chọn)
5. Click **Hoàn tất**

### Cấu hình Docker standalone

```yaml
services:
  wyoming-vietnamese-asr:
    image: gnolnos/wyoming-vietnamese-asr:latest
    container_name: wyoming-vietnamese-asr
    ports:
      - "10301:10301"  # Wyoming protocol
      - "8090:8090"    # FastAPI (tùy chọn)
    environment:
      - TZ=Asia/Saigon
      - MODEL_PATH=/app/model
    volumes:
      - ./model:/app/model:ro
    restart: unless-stopped
```

## 🎤 Sử dụng

### Trong Home Assistant

Sau khi cài đặt, tích hợp sẽ xuất hiện như một nhà cung cấp STT:

1. Vào **Cài đặt** → **Trợ lý giọng nói**
2. Chọn trợ lý của bạn
3. Chọn **"Vietnamese ASR"** làmengine **Speech-to-Text**
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
│  Cổng: 10301                            │
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

### Wyoming Server (chính)

```yaml
services:
  wyoming:
    image: gnolnos/wyoming-vietnamese-asr:latest
    ports:
      - "10301:10301"
    volumes:
      - ./model:/app/model:ro
    environment:
      - TZ=Asia/Saigon
    restart: unless-stopped
    # Bật GPU (nếu có):
    # devices:
    #   - /dev/dri:/dev/dri
```

### FastAPI Server (cho Xiaozzi)

```yaml
services:
  fastapi:
    image: gnolnos/wyoming-vietnamese-asr:fastapi
    ports:
      - "8090:8090"
    volumes:
      - ./model:/app/model:ro
    environment:
      - TZ=Asia/Saigon
    restart: unless-stopped
```

### Docker Compose đầy đủ

```bash
cd docker
docker compose up -d

# Kiểm tra trạng thái
docker compose ps

# Xem log
docker compose logs -f
```

## 🔧 Xử lý sự cố

### Kết nối thất bại

**Triệu chứng:** `Connection refused` hoặc `Timeout`

**Giải pháp:**
```bash
# Kiểm tra Wyoming server đang chạy
docker ps | grep wyoming

# Kiểm tra cổng
netstat -tlnp | grep 10301

# Test kết nối
nc -zv 192.168.100.150 10301
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
