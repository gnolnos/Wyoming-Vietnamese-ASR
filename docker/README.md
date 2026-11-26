# Wyoming Vietnamese ASR cho Home Assistant

[![GitHub Release](https://img.shields.io/github/v/release/gnolnos/wyoming-vietnamese-asr)](https://github.com/gnolnos/wyoming-vietnamese-asr/releases)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz/)

Vietnamese Automatic Speech Recognition (ASR) integration for Home Assistant using Wyoming protocol.

> 🇻🇳 **[Đọc bản tiếng Việt](README.vi.md)** | **[English version](README.md)**

## Features

- **Vietnamese ASR**: High-accuracy Vietnamese speech recognition (WER 7.97%)
- **Wyoming Protocol**: Native integration with Home Assistant's Wyoming STT
- **FastAPI Mode**: Optional REST API for external integrations (Xiaozhi, etc.)
- **GPU Acceleration**: NVIDIA GPU support for faster transcription
- **Docker Support**: Standalone deployment option (outside Home Assistant)

## Model

- **Model**: Zipformer-30M-RNNT-6000h
- **Language**: Vietnamese
- **WER**: 7.97% (VLSP2025 benchmark)
- **Provider**: [hynt/Zipformer-30M-RNNT-6000h](https://huggingface.co/hynt/Zipformer-30M-RNNT-6000h)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Search for "Wyoming Vietnamese ASR"
3. Click Install
4. Restart Home Assistant
5. Add integration via UI

### Manual

1. Download the latest release from [GitHub Releases](https://github.com/gnolnos/wyoming-vietnamese-asr/releases)
2. Extract `wyoming_vietnamese.zip` to `custom_components/wyoming_vietnamese/`
3. Restart Home Assistant
4. Add integration via UI

## Configuration

### Home Assistant Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Wyoming Vietnamese ASR"
4. Configure:
   - **Host**: Wyoming server IP (default: `192.168.100.150`)
   - **Port**: Wyoming server port (default: `10301`)
   - **Name**: Integration name (optional)

### Standalone Docker

```bash
# Clone repository
git clone https://github.com/gnolnos/wyoming-vietnamese-asr.git
cd wyoming-vietnamese-asr/docker

# Download model
mkdir model
# Download from HuggingFace and place in model/

# Start services
docker compose up -d
```

## Usage

### Home Assistant STT

Once configured, the integration will appear as an STT provider in Home Assistant:

1. Go to **Settings** → **Voice Assistants**
2. Select your assistant
3. Choose "Vietnamese ASR" as the **Speech-to-Text** engine
4. Start speaking Vietnamese!

### FastAPI (Xiaozzi Integration)

For external integrations like Xiaozhi:

```bash
# FastAPI server runs on port 8090
curl -X POST "http://localhost:8090/transcribe" \
  -H "Content-Type: audio/wav" \
  --data-binary @audio.wav
```

## Architecture

```
┌─────────────────────────────────────┐
│  Home Assistant (Voice Assistant)   │
│  Wyoming STT Integration            │
└──────────────┬──────────────────────┘
               │ Wyoming Protocol
               ▼
┌─────────────────────────────────────┐
│  Wyoming Vietnamese ASR Server      │
│  Port: 10301                        │
│  Model: Zipformer-30M-RNNT-6000h   │
└──────────────┬──────────────────────┘
               │ (optional)
               ▼
┌─────────────────────────────────────┐
│  FastAPI Server                     │
│  Port: 8090 (Xiaozhi, REST API)    │
└─────────────────────────────────────┘
```

## Docker Deployment

### Wyoming Server

```yaml
services:
  wyoming:
    image: gnolnos/wyoming-vietnamese-asr:latest
    ports:
      - "10301:10301"
    volumes:
      - ./model:/app/model:ro
    restart: unless-stopped
```

### FastAPI Server

```yaml
services:
  fastapi:
    image: gnolnos/wyoming-vietnamese-asr:fastapi
    ports:
      - "8090:8090"
    volumes:
      - ./model:/app/model:ro
    restart: unless-stopped
```

## Troubleshooting

### Connection Refused

- Ensure Wyoming server is running on the specified host:port
- Check firewall rules
- Verify service status: `docker ps | grep wyoming`

### Poor Transcription Quality

- Ensure audio input is clear Vietnamese speech
- Check microphone settings in Home Assistant
- Verify model is loaded correctly

### Performance Issues

- Enable GPU acceleration (NVIDIA)
- Increase memory allocation (2GB+ recommended)
- Use SSD storage for model files

## Development

### Build Docker Image

```bash
docker build -t wyoming-vietnamese-asr -f docker/Dockerfile .
```

### Run Tests

```bash
python -m pytest tests/
```

## License

MIT License - See [LICENSE](LICENSE) for details.

## Credits

- Model: [hynt/Zipformer-30M-RNNT-6000h](https://huggingface.co/hynt/Zipformer-30M-RNNT-6000h)
- Wyoming Protocol: [Home Assistant](https://www.home-assistant.io/integrations/wyoming/)
- Integration: [gnolnos](https://github.com/gnolnos)
