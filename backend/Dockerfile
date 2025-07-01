FROM python:3.12-slim-bookworm

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv

COPY pyproject.toml .
COPY uv.lock .
RUN uv pip install --no-deps . --system 

RUN uv pip list | grep -q gunicorn || \
    (echo "Gunicorn not found by uv pip list, attempting explicit install..." && \
     uv pip install gunicorn --system && \
     uv pip list | grep -q gunicorn || \
     (echo "Error: gunicorn could not be installed even explicitly!" && exit 1)) && \
    echo "Gunicorn successfully installed by uv."

ENV PATH="/usr/local/bin:/usr/local/sbin:/usr/local/lib/python3.12/site-packages/bin:/root/.local/bin:${PATH}"

COPY app/ app/

# Gunicornを使ってFlaskアプリを起動
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "app.app:app"]
