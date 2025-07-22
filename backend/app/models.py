from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, JSON, Date
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    age = Column(String(10))
    gender = Column(String(10))
    preferred_style = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)

    clothes = relationship("Cloth", back_populates="user")
    suggestions = relationship("OutfitSuggestion", back_populates="user")
    preferences = relationship("UserPreference", back_populates="user", uselist=False)

class Cloth(Base):
    __tablename__ = 'clothes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False) # 例: 'トップス', 'ボトムス', 'アウター', 'シューズ', 'アクセサリー'
    color = Column(String(255), nullable=False)
    material = Column(String(255))
    season = Column(String(255)) # 例: '春,夏', '秋,冬'
    is_formal = Column(Boolean, default=False)
    available = Column(Boolean, default=True)
    preferred = Column(Boolean, default=False)
    image_url = Column(String(255))
    vector = Column(JSON) # JSONとしてベクトルを保存。または別途ベクトルDBへ

    user = relationship("User", back_populates="clothes")

class OutfitSuggestion(Base):
    __tablename__ = 'outfit_suggestions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    suggested_date = Column(Date, nullable=False)
    top_id = Column(Integer, ForeignKey('clothes.id'))
    bottom_id = Column(Integer, ForeignKey('clothes.id'))
    outer_id = Column(Integer, ForeignKey('clothes.id'))
    # 他のアイテムのIDを追加するならここへ
    weather_info = Column(String(255))
    occasion_info = Column(String(255)) # 外出先、会う相手
    suggested_at = Column(DateTime, default=func.now())
    feedback_rating = Column(Integer) # ユーザーからの評価 (1-5など)

    user = relationship("User", back_populates="suggestions")
    top = relationship("Cloth", foreign_keys=[top_id])
    bottom = relationship("Cloth", foreign_keys=[bottom_id])
    outer = relationship("Cloth", foreign_keys=[outer_id])

class UserPreference(Base):
    __tablename__ = 'user_preferences'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    personal_color = Column(String(255))
    body_shape = Column(String(255))
    disliked_colors = Column(String(255)) # 例: "赤,緑"
    disliked_styles = Column(String(255)) # 例: "カジュアル,パンク"

    user = relationship("User", back_populates="preferences")