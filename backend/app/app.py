from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
from sqlalchemy import text
from flask_jwt_extended import JWTManager
import os

from flask_migrate import Migrate

# Models and Database imports
from .models import Base, User, Cloth, OutfitSuggestion, UserPreference
from app.database import engine, SessionLocal, get_db_session, close_db_session, DATABASE_URL

# Blueprint imports
from app.routes.auth import auth_bp
from app.routes.clothing import clothing_bp
from app.routes.suggestion import suggestion_bp
from app.routes.chat import chat_bp
from app.routes.upload import upload_bp

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER_PATH = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER_PATH):
    os.makedirs(UPLOAD_FOLDER_PATH)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER_PATH

# Flask config for DB
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['DATABASE_URL'] = DATABASE_URL

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

jwt = JWTManager(app)

migrate = Migrate(app, Base.metadata)

app.register_blueprint(auth_bp)
app.register_blueprint(clothing_bp)
app.register_blueprint(suggestion_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(upload_bp)

# Database session management
@app.teardown_request
def teardown_db_session(exception):
    close_db_session(exception)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Health check
@app.route('/')
def health_check():
    session = get_db_session()
    try:
        with session.connection() as connection:
            result = connection.execute(text("SELECT 1"))
            if result.scalar() == 1:
                return jsonify({"status": "ok", "db_connection": "successful"}), 200
            else:
                return jsonify({"status": "error", "db_connection": "failed"}), 500
    except Exception as e:
        return jsonify({"status": "error", "db_connection": f"failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)