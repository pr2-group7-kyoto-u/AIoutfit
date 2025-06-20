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
        # 参照整合性の関係で、参照している子テーブルから削除する必要がある
        session.query(OutfitSuggestion).delete()
        session.query(Cloth).delete()
        session.query(UserPreference).delete()
        session.query(User).delete()
        session.commit()
        print("Existing data cleared.")

        # --- ユーザーの追加 ---
        user1_password_hash = generate_password_hash("password123")
        user1 = User(username="testuser1", password_hash=user1_password_hash, preferred_style="カジュアル, シンプル")
        session.add(user1)
        session.commit() # user1のIDを確定させるため一度コミット

        user2_password_hash = generate_password_hash("securepass")
        user2 = User(username="stylish_dev", password_hash=user2_password_hash, preferred_style="きれいめ, モード")
        session.add(user2)
        session.commit() # user2のIDを確定させるため一度コミット

        print(f"Added users: {user1.username} (ID: {user1.id}), {user2.username} (ID: {user2.id})")

        # --- ユーザーの好みを追加 ---
        user1_pref = UserPreference(user=user1, personal_color="イエベ春", body_shape="ウェーブ", disliked_colors="緑", disliked_styles="パンク")
        user2_pref = UserPreference(user=user2, personal_color="ブルベ夏", body_shape="ストレート", disliked_colors="茶色")
        session.add_all([user1_pref, user2_pref])
        session.commit()
        print("Added user preferences.")

        # --- 服の追加 (user1) ---
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

        # --- 服の追加 (user2) ---
        clothes_user2 = [
            Cloth(user=user2, name="ネイビーのジャケット", category="アウター", color="ネイビー", material="ポリエステル", season="春,秋,冬", is_formal=True, image_url="https://example.com/jacket_navy.jpg"),
            Cloth(user=user2, name="白いブラウス", category="トップス", color="白", material="レーヨン", season="春,夏,秋", is_formal=True, image_url="https://example.com/blouse_white.jpg"),
            Cloth(user=user2, name="グレーのスラックス", category="ボトムス", color="グレー", material="ウール", season="秋,冬", is_formal=True, image_url="https://example.com/slacks_grey.jpg"),
            Cloth(user=user2, name="黒のパンプス", category="シューズ", color="黒", material="レザー", season="春,夏,秋,冬", is_formal=True, image_url="https://example.com/pumps_black.jpg"),
        ]
        session.add_all(clothes_user2)
        session.commit()
        print(f"Added {len(clothes_user2)} clothes for {user2.username}.")

        print("Database seeding completed successfully.")

    except Exception as e:
        session.rollback()
        print(f"Error during seeding: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    seed_data()