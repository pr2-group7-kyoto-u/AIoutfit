# 毎日コーディネートアプリ

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen)](https://github.com/pr2-group7-kyoto-u/AIoutfit/actions) 
## 1. はじめに

このプロジェクトは、ユーザーの持つ服の情報、その日の天気や外出先に基づいて、最適なコーディネートを提案するWebアプリケーションです。
React（TypeScript）製のフロントエンド、Flask（Python）製のバックエンド、およびMySQLデータベースで構成されており、これら全てはDocker Composeを使用してコンテナとして実行されます。

## 2. プロジェクトの構造(一部省略)
```
daily-outfit-app/
├── backend/                  # Flaskバックエンドアプリケーション
│   ├── app/                  # FlaskアプリケーションのPythonコード
│   │   ├── seed.py           # seedファイル
│   │   ├── app.py            # アプリケーションのエントリーポイント
│   │   ├── models.py         # SQLAlchemyモデル定義（DBスキーマ）
│   │   ├── routes.py         # APIエンドポイント定義
│   │   └── utils.py          # LLM連携、外部API連携など
│   ├── migrations/           # DBマイグレーションファイル (Alembic)
│   ├── Dockerfile            # バックエンド用Dockerファイル
│   └── requirements.txt      # Python依存関係
├── frontend/                 # Reactフロントエンドアプリケーション
│   ├── public/               # 公開静的ファイル (index.htmlなど)
│   ├── src/                  # Reactソースコード
│   │   ├── api/              # API呼び出しロジック
│   │   ├── components/       # 再利用可能なUIコンポーネント
│   │   ├── pages/            # 各ページコンポーネント
│   │   ├── index.tsx         # 実行ファイル
│   │   └── App.tsx           # ルーティング定義
│   ├── Dockerfile            # フロントエンド用Dockerファイル (Nginxも含む)
│   ├── nginx.conf            # Nginx設定ファイル
│   ├── package.json          # Node.js依存関係
│   └── tsconfig.json         # TypeScript設定
├── mysql/                    # MySQLデータベース設定
│   └── init.sql              # MySQL初期化スクリプト (DB/ユーザー作成のみ)
├── .env                      # 環境変数 (Git管理から除外)
├── .env.example              # 環境変数の例 (Git管理)
├── .gitignore                # Gitが無視するファイル/ディレクトリ
└── docker-compose.yml        # Docker Compose設定ファイル
```

## 3. 前提条件

環境構築を始める前に、以下のツールがローカルマシンにインストールされていることを確認してください。

* **Git**: ソースコードをクローンするために必要です。
    * [Git 公式サイト](https://git-scm.com/downloads) からダウンロード・インストールしてください。
* **Docker Desktop**: Dockerコンテナを管理・実行するために必要です。
    * [Docker Desktop 公式サイト](https://www.docker.com/products/docker-desktop/) からダウンロード・インストールしてください。
    * **Windowsユーザーは、WSL 2の有効化と設定が必要です。** Docker Desktopのインストール時に指示に従うか、[公式ドキュメント](https://docs.docker.com/desktop/install/windows-install/#wsl-2-backend) を参照してください。

## 4. 環境構築手順

### 4.1. プロジェクトの取得

まず、GitHubリポジトリからプロジェクトのソースコードをローカルにクローンします。

1.  ターミナルまたはコマンドプロンプトを開きます。
2.  プロジェクトを配置したいディレクトリに移動します（例: ドキュメントフォルダなど）。
    ```bash
    # 例: Windows PowerShell
    cd C:\Users\YourUser\Documents
    # 例: macOS/Linux
    cd ~/Documents
    ```
3.  以下のコマンドでリポジトリをクローンします。
    ```bash
    git clone [https://github.com/pr2-group7-kyoto-u/AIoutfit.git](https://github.com/pr2-group7-kyoto-u/AIoutfit.git)
    ```
4.  クローンしたプロジェクトのルートディレクトリに移動します。
    クローンにより `AIoutfit` というディレクトリが作成されます。
    ```bash
    cd AIoutfit
    ```
    **これ以降の全てのコマンドは、この `AIoutfit` ディレクトリ（`docker-compose.yml` がある場所）で実行します。**

### 4.2. 環境変数の設定

プロジェクトは環境変数を `.env` ファイルから読み込みます。

1.  プロジェクトルートディレクトリに、`** .env.example**` というファイルがあることを確認します。
2.  このファイルをコピーして、`** .env**` という名前で保存します。
    * Windows PowerShell: `Copy-Item .env.example .env`
    * macOS/Linux: `cp .env.example .env`
3.  `** .env**` ファイルをテキストエディタで開き、以下の変数を適切に設定します。

    ```ini
    # .env
    # MySQL Configuration
    MYSQL_ROOT_PASSWORD=your_root_password_here # <-- 任意のパスワードを設定してください (例: my_root_password)
    MYSQL_DATABASE=outfit_db
    MYSQL_USER=outfit_user
    MYSQL_PASSWORD=outfit_password

    # External API Keys (Optional, uncomment and fill if used)
    # LLM_API_KEY=your_llm_api_key_here
    # WEATHER_API_KEY=your_weather_api_key_here
    ```your_root_password_here` は開発用として分かりやすいパスワードに設定して構いません。

### 4.3. Docker環境の構築と起動

Docker Composeを使用して、アプリケーションのサービス（MySQL, Flaskバックエンド, Reactフロントエンド）を構築・起動します。

1.  **Docker Desktop が起動していることを確認します。**
    * タスクバーの通知領域（Windows）またはメニューバー（Mac）にあるDockerアイコンが、緑色または青色で「Docker Desktop is running」と表示されていることを確認してください。

2.  **Dockerイメージの構築とコンテナの起動:**
    プロジェクトルートディレクトリで、以下のコマンドを実行します。
    **初回はDockerイメージのダウンロードと構築に時間がかかります（数分〜数十分）。**

    ```bash
    docker compose up --build -d
    ```
    * `--build`: Dockerイメージがまだない場合やDockerfileに変更があった場合に、イメージを構築します。
    * `-d`: コンテナをバックグラウンド（デタッチモード）で起動し、ターミナルを解放します。

3.  **コンテナが正常に起動していることを確認:**
    上記コマンド実行後、数秒待ってから、以下のコマンドでコンテナの状態を確認します。
    `State` 列がすべて `running (healthy)` または `running` になっていればOKです。

    ```bash
    docker compose ps
    ```
    もし `State` が `exited` や `unhealthy` の場合、何らかのエラーが発生しています。`docker compose logs [サービス名]` (例: `docker compose logs db`) コマンドでログを確認し、トラブルシューティングしてください。

#### 4.3.1. フロントエンドの依存関係のインストール（`npm install` について）

通常、`docker compose up --build -d` コマンドを実行する際、`frontend/Dockerfile` のビルドステップで自動的に `npm install` が実行されます。そのため、**基本的な環境構築において、開発者が手動で `npm install` を実行する必要はありません。**

ただし、以下のような場合には手動での `npm install` が必要となることがあります。

* **Dockerコンテナを使わず、ローカルマシンで直接フロントエンドの開発を行う場合**（例: `cd frontend && npm start`）。
* **新しいNode.jsパッケージ（ライブラリ）を `package.json` に追加した場合**。
* **既存の依存関係を最新バージョンに更新したい場合**（`npm update`）。
* 何らかの理由でDockerのビルドキャッシュが壊れ、コンテナ内の `node_modules` が不完全になった可能性がある場合。

手動で `npm install` を実行する場合は、`frontend` ディレクトリに移動してからコマンドを実行してください。

```bash
cd frontend
npm install
cd .. # 作業後、必ずプロジェクトルートに戻る
```


### 4.4. データベースの初期化とマイグレーション

アプリケーションのデータベーススキーマを設定します。

1.  **データベーススキーマの適用:**
    Gitリポジトリに既に存在するマイグレーションファイル（`migrations/versions/` ディレクトリ内）を基に、データベーステーブルを構築します。
    **これは、プロジェクトをGitからクローンしてきて環境構築を行う全てのユーザー（開発者）が必要な手順です。**
    **必ず、MySQLコンテナ（`daily-outfit-db`）が `running (healthy)` 状態になってから、以下のコマンドを実行してください。** (`docker compose ps` で確認できます)

    ```bash
    docker exec -it daily-outfit-backend sh -c "FLASK_APP=app.app flask db upgrade"
    ```
    このコマンドは、データベースにアプリケーションのテーブル（`users`, `clothes` など）を作成します。エラーなくプロンプトが戻ってくれば成功です。

2.  **開発中のスキーマ変更と新しいマイグレーションファイルの生成:**
    **これは、あなたが `backend/app/models.py` を変更し、データベースのスキーマに新しい変更を加えた場合にのみ必要な手順です。**
    変更を反映するための新しいマイグレーションファイルを生成します。

    ```bash
    docker exec -it daily-outfit-backend sh -c "FLASK_APP=app.app flask db migrate -m 'あなたの変更内容を説明するメッセージ'"
    ```
    生成されたマイグレーションファイルはGitにコミットし、チームメンバーと共有してください。その後、上記と同じ `flask db upgrade` コマンドで変更を適用します。

3.  **シードデータ（テストデータ）の投入**
    アプリケーションをテストするためのダミーデータをデータベースに投入します。

    ```bash
    docker exec -it daily-outfit-backend python -m app.seed
    ```
    `Seeding database...` のようなメッセージが表示され、エラーなくプロンプトが戻ってくれば成功です。

## 5. アプリケーションへのアクセス

すべてのサービスが起動し、データベースの初期設定が完了したら、Webブラウザからアプリケーションにアクセスできます。

* **フロントエンドURL**: `http://localhost:80/`

ブラウザでこのURLを開き、アプリケーションのログイン/登録画面が表示されることを確認してください。

## 6. その他の便利コマンド

プロジェクトルートディレクトリで実行します。

* **コンテナのログを見る:**
    * すべてのログ: `docker compose logs`
    * 特定のサービスのログ: `docker compose logs [サービス名] ` (例: `docker compose logs backend`)
    * リアルタイムでログを追跡: `docker compose logs -f [サービス名] ` (例: `docker compose logs -f frontend`)
* **コンテナを停止する（データを保持する場合）:**
    ```bash
    docker compose down
    ```
    次回 `docker compose up -d` で起動すると、データは保持されています。
* **コンテナとデータを完全に削除する（初期状態に戻す）:**
    開発中にデータベースの状態を完全にリセットしたい場合にのみ使用します。
    ```bash
    docker compose down -v
    ```
    このコマンドを実行すると、MySQLのデータベースデータも完全に削除されます。再度 `docker compose up --build -d` と `flask db upgrade` を実行し直す必要があります。
* **特定のコンテナのシェルに入る:**
    デバッグや手動での操作に役立ちます。
    ```bash
    docker exec -it daily-outfit-backend bash # Flaskバックエンドのシェル
    docker exec -it daily-outfit-db bash      # MySQLデータベースのシェル
    ```

## 8. uvの利用法
* uvのインストール
```
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

* ディレクトリ移動
```
cd backend
```
* ライブラリのインストール
```
uv sync
```

* プログラムの実行

`python`の代わりに`uv run`で実行してください

e.g
```
uv run main.py
```
## 7. トラブルシューティング

もし問題が発生した場合、以下の情報を添えて、チームメンバーやメンターに相談してください。

* **実行したコマンド**
* **表示されたエラーメッセージの全文**
* **`docker compose ps` の出力**
* **`docker compose logs [問題のあるサービス名]` の出力**
* **使用しているOSとDocker Desktopのバージョン**