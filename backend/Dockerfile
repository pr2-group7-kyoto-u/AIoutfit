# backend/Dockerfile
FROM python:3.12-slim-bookworm

WORKDIR /app

# JWT_SECRET_KEY をビルド引数として受け取り、環境変数として設定
# Docker Compose の .env からビルド時に値が渡される
ARG JWT_SECRET_KEY
ENV JWT_SECRET_KEY=${JWT_SECRET_KEY}

# uv installation
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv

COPY pyproject.toml .
COPY uv.lock .
RUN uv pip install . --system

# PATH for executables
ENV PATH="/usr/local/bin:/usr/local/sbin:/usr/local/lib/python3.12/site-packages/bin:/root/.local/bin:${PATH}"

# Application code
COPY app/ app/

# Gunicorn CMD
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--log-level", "debug", "--access-logfile", "-", "app.app:app"]