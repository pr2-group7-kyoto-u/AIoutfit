from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError
from app.database import get_db_session
from app.models import User
import traceback
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/register', methods=['POST'])
def register():
    session = get_db_session()
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        if not username or not password:
            return jsonify({"message": "Username and password are required"}), 400
        if session.query(User).filter_by(username=username).first():
            return jsonify({"message": "Username already exists"}), 409

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password)
        session.add(new_user)
        session.commit()

        access_token = create_access_token(identity=str(new_user.id))
        
        return jsonify({
            "message": "User registered successfully",
            "user_id": new_user.id,
            "username": new_user.username,
            "access_token": access_token
        }), 201
    except Exception as e:
        session.rollback()
        print("--- FATAL ERROR IN /api/register ---", flush=True)
        print(traceback.format_exc(), flush=True)
        return jsonify({"message": "An unexpected server error occurred."}), 500

@auth_bp.route('/api/login', methods=['POST'])
def login():
    session = get_db_session()
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        user = session.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            
            access_token = create_access_token(identity=str(user.id))

            return jsonify({
                "message": "Login successful",
                "user_id": user.id,
                "username": user.username,
                "access_token": access_token
            }), 200
        else:
            return jsonify({"message": "Invalid credentials"}), 401
    except Exception as e:
        session.rollback()
        print("--- FATAL ERROR IN /api/login ---", flush=True)
        print(traceback.format_exc(), flush=True)
        return jsonify({"message": f"An unexpected server error occurred."}), 500

# デバッグ用エンドポイント
@auth_bp.route('/api/debug/verify_token', methods=['GET'])
@jwt_required()
def debug_verify_token():
    try:
        current_user_id = get_jwt_identity()
        print(f"--- DEBUG: Token verification successful ---", flush=True)
        print(f"--- DEBUG: Identity from token: {current_user_id} (type: {type(current_user_id)}) ---", flush=True)
        return jsonify(message="Token is valid", identity=current_user_id), 200
    except Exception as e:
        print(f"--- DEBUG: Error inside verify_token endpoint: {e} ---", flush=True)
        return jsonify(message=f"An error occurred: {str(e)}"), 500