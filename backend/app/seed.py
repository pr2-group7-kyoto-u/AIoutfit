# backend/app/seed.py
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash
import datetime

from app.models import Base, User, Cloth, OutfitSuggestion, UserPreference


DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://outfit_user:outfit_password@db:3306/outfit_db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def seed_data():
    session = Session()
    try:
        print("Seeding database...")

        # --- 既存データを削除 (開発時のみ) ---
        # テーブルが存在しない場合にエラーになるのを避けるため、コメントアウト
        # 通常は flask db upgrade でテーブルが作成された後に実行されるべき
        # session.query(OutfitSuggestion).delete()
        # session.query(Cloth).delete()
        # session.query(UserPreference).delete()
        # session.query(User).delete()
        # session.commit()
        # print("Existing data cleared.")
        print("Skipping existing data cleanup (tables might not exist yet).")


        # --- ユーザーの追加 ---
        # ユーザーが既に存在しないかチェックしてから追加する（冪等性を高める）
        if not session.query(User).filter_by(username="testuser1").first():
            user1_password_hash = generate_password_hash("password123")
            user1 = User(username="testuser1", password_hash=user1_password_hash, age="25", gender="男性", preferred_style="カジュアル, シンプル")
            session.add(user1)
            session.commit()
            print(f"Added user: {user1.username} (ID: {user1.id})")
        else:
            user1 = session.query(User).filter_by(username="testuser1").first()
            print(f"User testuser1 already exists (ID: {user1.id}). Skipping.")

        if not session.query(User).filter_by(username="stylish_dev").first():
            user2_password_hash = generate_password_hash("securepass")
            user2 = User(username="stylish_dev", password_hash=user2_password_hash, age="30", gender="女性", preferred_style="きれいめ, モード")
            session.add(user2)
            session.commit()
            print(f"Added user: {user2.username} (ID: {user2.id})")
        else:
            user2 = session.query(User).filter_by(username="stylish_dev").first()
            print(f"User stylish_dev already exists (ID: {user2.id}). Skipping.")


        # --- ユーザーの好みを追加 ---
        # ユーザーの好みが既に存在しないかチェックしてから追加する
        if not session.query(UserPreference).filter_by(user_id=user1.id).first():
            user1_pref = UserPreference(user=user1, personal_color="イエベ春", body_shape="ウェーブ", disliked_colors="緑", disliked_styles="パンク")
            session.add(user1_pref)
            print("Added user1 preferences.")
        else:
            print("User1 preferences already exist. Skipping.")

        if not session.query(UserPreference).filter_by(user_id=user2.id).first():
            user2_pref = UserPreference(user=user2, personal_color="ブルベ夏", body_shape="ストレート", disliked_colors="茶色")
            session.add(user2_pref)
            print("Added user2 preferences.")
        else:
            print("User2 preferences already exist. Skipping.")
        session.commit() # 好みもコミット


        # --- 服の追加 (user1) ---
        # 服が既に存在しないかチェックしてから追加する (簡易的なチェック)
        if not session.query(Cloth).filter_by(user_id=user1.id, name="白い半袖Tシャツ").first():
            clothes_user1 = [
                Cloth(user=user1, name="白い半袖Tシャツ", category="トップス", color="白", material="綿", season="春,夏", is_formal=False, image_url="https://example.com/tshirt_white.jpg"),
                Cloth(user=user1, name="ブルージーンズ", category="ボトムス", color="青", material="デニム", season="春,夏,秋,冬", is_formal=False, image_url="https://example.com/jeans_blue.jpg"),
                Cloth(user=user1, name="黒いパーカー", category="アウター", color="黒", material="フリース", season="春,秋,冬", is_formal=False, image_url="https://example.com/hoodie_black.jpg"),
                Cloth(user=user1, name="ベージュのチノパン", category="ボトムス", color="ベージュ", material="綿", season="春,夏,秋", is_formal=False, image_url="https://example.com/chino_beige.jpg"),
                Cloth(user=user1, name="白いスニーカー", category="シューズ", color="白", material="キャンバス", season="春,夏,秋", is_formal=False, image_url="https://example.com/sneaker_white.jpg"),
            ]
            session.add_all(clothes_user1)
            session.commit()
            print(f"Added {len(clothes_user1)} clothes for {user1.username}.")
        else:
            print(f"Clothes for {user1.username} already exist. Skipping.")


        # --- 服の追加 (user2) ---
        if not session.query(Cloth).filter_by(user_id=user2.id, name="ネイビーのジャケット").first():
            clothes_user2 = [
                Cloth(user=user2, name="ネイビーのジャケット", category="アウター", color="ネイビー", material="ポリエステル", season="春,秋,冬", is_formal=True, image_url="https://example.com/jacket_navy.jpg"),
                Cloth(user=user2, name="白いブラウス", category="トップス", color="白", material="レーヨン", season="春,夏,秋", is_formal=True, image_url="https://example.com/blouse_white.jpg"),
                Cloth(user=user2, name="グレーのスラックス", category="ボトムス", color="グレー", material="ウール", season="秋,冬", is_formal=True, image_url="https://example.com/slacks_grey.jpg"),
                Cloth(user=user2, name="黒のパンプス", category="シューズ", color="黒", material="レザー", season="春,夏,秋,冬", is_formal=True, image_url="https://example.com/pumps_black.jpg"),
            ]
            session.add_all(clothes_user2)
            session.commit()
            print(f"Added {len(clothes_user2)} clothes for {user2.username}.")
        else:
            print(f"Clothes for {user2.username} already exist. Skipping.")


        print("Database seeding completed successfully.")

    except Exception as e:
        session.rollback()
        # テーブルが存在しないエラーの場合は、より分かりやすいメッセージを出す
        if "Table" in str(e) and "doesn't exist" in str(e):
            print(f"Error during seeding: Tables might not be created yet. Please ensure 'flask db upgrade' has been run successfully. Detail: {e}")
        else:
            print(f"Error during seeding: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    seed_data()