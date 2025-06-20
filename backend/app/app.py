from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

from flask_migrate import Migrate

from .models import Base, User, Cloth, OutfitSuggestion, UserPreference
from .routes import register_routes

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://outfit_user:outfit_password@db:3306/outfit_db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL 
app.config['DATABASE_URL'] = DATABASE_URL

migrate = Migrate(app, Base.metadata)

register_routes(app, Session)

@app.route('/')
def health_check():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            if result.scalar() == 1:
                return jsonify({"status": "ok", "db_connection": "successful"}), 200
            else:
                return jsonify({"status": "error", "db_connection": "failed"}), 500
    except Exception as e:
        return jsonify({"status": "error", "db_connection": f"failed: {str(e)}"}), 500

if __name__ == '__main__':
    # 開発環境でのみ使用。本番ではGunicornが起動する
    app.run(debug=True, host='0.0.0.0', port=5000)