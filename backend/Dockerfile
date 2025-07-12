# Pythonの公式イメージをベースに使用
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージをインストール
# uvを先にインストール
RUN pip install uv

# pyproject.tomlとuv.lockをコピー
COPY pyproject.toml uv.lock* ./

# uvを使って依存関係をインストール
RUN uv pip install --system --no-cache -r pyproject.toml

# アプリケーションのコードをコピー
COPY . .

# ★★★ entrypoint.shをコピーし、実行権限を付与 ★★★
COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# コンテナ起動時にentrypoint.shを実行するように設定
ENTRYPOINT ["/app/entrypoint.sh"]
