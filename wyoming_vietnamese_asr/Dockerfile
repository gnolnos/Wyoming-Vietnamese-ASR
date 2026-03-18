# Wyoming Vietnamese ASR Add-on
ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install dependencies
RUN apk add --no-cache \
    py3-pip \
    ffmpeg \
    libsndfile \
    py3-numpy

# Set working directory
WORKDIR /app

# Install Python packages
RUN pip3 install --no-cache-dir \
    wyoming==1.5.0 \
    soundfile==0.12.1 \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    onnxruntime==1.16.3

# Labels
LABEL \
    io.hass.name="Wyoming Vietnamese ASR" \
    io.hass.description="Vietnamese Automatic Speech Recognition using Wyoming protocol. Model: Zipformer-30M-RNNT-6000h (WER 7.97%)." \
    io.hass.arch="amd64|aarch64" \
    io.hass.type="addon" \
    io.hass.version="1.0.0" \
    org.opencontainers.image.title="Wyoming Vietnamese ASR" \
    org.opencontainers.image.description="Vietnamese ASR for Home Assistant" \
    org.opencontainers.image.vendor="gnolnos" \
    org.opencontainers.image.authors="gnolnos <https://github.com/gnolnos>" \
    org.opencontainers.image.url="https://github.com/gnolnos/Wyoming-Vietnamese-ASR" \
    org.opencontainers.image.source="https://github.com/gnolnos/Wyoming-Vietnamese-ASR"

USER root

WORKDIR /app

# Copy server files
COPY server/ ./server/
COPY run.sh /run.sh
RUN chmod a+x /run.sh

# Create model directory
RUN mkdir -p /data

EXPOSE 10400 8090

CMD ["/run.sh"]
