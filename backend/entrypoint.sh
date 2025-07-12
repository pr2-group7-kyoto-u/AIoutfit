#!/bin/sh

# いずれかのコマンドが失敗した場合、即座にスクリプトを終了する
set -e

# Flask-MigrateがFlaskアプリケーションを認識できるように環境変数を設定
export FLASK_APP=app.app

echo "Waiting for database to be ready..."
# ここでDBの準備が整うまで待つ処理を入れるとより堅牢になりますが、
# docker-composeのdepends_onで代用しているため、今回は省略します。

# データベースのマイグレーションを適用
# これにより、models.pyの定義に基づいてテーブルが作成・更新されます
echo "Applying database migrations..."
flask db upgrade

# Gunicornサーバーを起動して、アプリケーションを実行
echo "Starting Gunicorn server..."
exec gunicorn --config /app/gunicorn.conf.py app.app:app
