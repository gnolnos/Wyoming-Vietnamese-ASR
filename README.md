# 🧠 Wyoming Vietnamese ASR - Home Assistant Add-on

[![GitHub Release](https://img.shields.io/github/v/release/gnolnos/wyoming-vietnamese-asr)](https://github.com/gnolnos/wyoming-vietnamese-asr/releases)
[![Docker](https://img.shields.io/docker/pulls/gnolnos/wyoming-vietnamese-asr)](https://hub.docker.com/r/gnolnos/wyoming-vietnamese-asr)

**🔊 Add-on Home Assistant cho nhận dạng giọng nói tiếng Việt (ASR) sử dụng Wyoming protocol.**

**[English](README-EN.md)** | **Tiếng Việt**

---

## 🚀 Cài đặt nhanh (1-click)

### Cách 1: Thêm Repository tự động

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fgnolnos%2FWyoming-Vietnamese-ASR)

**→ Click để thêm repository tự động!**

### Cách 2: Thêm thủ công

1. Mở **Home Assistant** → **Settings** → **Apps** → **App Store**
2. Click **⋮** (3 chấm) → **Repositories**
3. Paste:
   ```
   https://github.com/gnolnos/Wyoming-Vietnamese-ASR
   ```
4. Click **Add**
5. Tìm **Wyoming Vietnamese ASR** → **Install**
6. **Start** add-on

---

## 📊 Thông tin

| Thông số | Giá trị |
|----------|---------|
| **Model** | Zipformer-30M-RNNT-6000h |
| **Ngôn ngữ** | Tiếng Việt |
| **WER** | 7.97% (VLSP2025) |
| **Cổng** | 10400 (Wyoming), 8090 (FastAPI) |
| **Architecture** | amd64, aarch64 |

---

## ⚙️ Cấu hình sau khi cài

1. Mở **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Tìm **"Wyoming"**
4. Enter host: `localhost` và port: `10400`
5. Click **Submit**

---

## 🎯 Tính năng chính

- 🇻🇳 **Nhận dạng tiếng Việt chính xác** - WER 7.97%
- 🏠 **Add-on Home Assistant** - Cài đặt 1-click
- ⚡ **Độ trễ thấp** - Xử lý real-time
- 🔌 **Wyoming protocol** - Tích hợp native với HA Voice
- 🐳 **Docker** - Chạy standalone (xem [README-EN](README-EN.md))

---

## 🔗 Liên kết

- **Repository:** [github.com/gnolnos/Wyoming-Vietnamese-ASR](https://github.com/gnolnos/Wyoming-Vietnamese-ASR)
- **Docker Hub:** [hub.docker.com/r/gnolnos/wyoming-vietnamese-asr](https://hub.docker.com/r/gnolnos/wyoming-vietnamese-asr)
- **Model:** [huggingface.co/hynt/Zipformer-30M-RNNT-6000h](https://huggingface.co/hynt/Zipformer-30M-RNNT-6000h)

---

## 👨‍💻 Tác giả & Credits

**Integration:** [gnolnos](https://github.com/gnolnos) - Phan Sơn Long

**Model:** [hynt (HuggingFace)](https://huggingface.co/hynt/Zipformer-30M-RNNT-6000h) - Zipformer-30M-RNNT-6000h

**Wyoming Protocol:** [Home Assistant](https://www.home-assistant.io/integrations/wyoming/)

---

**⭐ Star repository để ủng hộ nếu thấy hữu ích!**
