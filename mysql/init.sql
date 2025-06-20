-- データベースが存在しない場合に作成
CREATE DATABASE IF NOT EXISTS outfit_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ユーザーが存在しない場合に作成し、権限を付与
CREATE USER IF NOT EXISTS 'outfit_user'@'%' IDENTIFIED BY 'outfit_password';
GRANT ALL PRIVILEGES ON outfit_db.* TO 'outfit_user'@'%';
FLUSH PRIVILEGES;

-- データベースを使用
USE outfit_db;
