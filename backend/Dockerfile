# Pythonの公式イメージをベースに使用
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
RUN pip install uv

# pyproject.tomlとuv.lockをコピー
COPY pyproject.toml uv.lock* ./

# uvを使って依存関係をインストール
RUN uv pip install --system --no-cache -r pyproject.toml

# アプリケーションのコードをコピー
COPY . .

# Flaskアプリの環境変数を設定（flask db upgradeに必要）
ENV FLASK_APP=app.app

# マイグレーション → Gunicorn 起動（ && を使って一行で）
ENTRYPOINT flask db upgrade && gunicorn --config /app/gunicorn.conf.py app.app:app
