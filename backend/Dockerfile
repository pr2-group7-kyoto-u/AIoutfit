FROM python:3.9-slim-buster

WORKDIR /app

# 依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY app/ app/

# Gunicornを使ってFlaskアプリを起動
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app.app:app"]