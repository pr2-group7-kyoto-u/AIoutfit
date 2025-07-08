from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from flask import g
import os

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://outfit_user:outfit_password@db:3306/outfit_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# リクエストごとにセッションを取得するヘルパー関数
def get_db_session():
    if 'db_session' not in g:
        g.db_session = SessionLocal()
    return g.db_session

# リクエストの終了時にセッションをクローズする関数
# この関数はapp.pyでapp.teardown_requestに登録する必要がある
def close_db_session(exception=None):
    session = g.pop('db_session', None)
    if session is not None:
        session.close()

# 初期化時にエンジンがDBに接続できるかテストする関数 (オプション)
def test_db_connection():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False