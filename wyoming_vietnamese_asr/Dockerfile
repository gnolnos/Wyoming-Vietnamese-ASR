# Wyoming Vietnamese ASR Add-on - Minimal build
ARG BUILD_FROM
FROM ${BUILD_FROM}

# Set working directory
WORKDIR /app

# Copy only required files (no pip install at build time)
COPY server/ ./server/
COPY download_model.py /app/download_model.py
COPY requirements.txt /app/requirements.txt
COPY run.sh /run.sh

RUN chmod a+x /run.sh

# Create data directory for models
RUN mkdir -p /data

EXPOSE 10400 8090

CMD ["/run.sh"]
