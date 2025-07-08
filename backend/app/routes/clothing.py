from flask import Blueprint, request, jsonify
from app.app import get_db_session
from app.models import Cloth, User
from flask_jwt_extended import jwt_required, get_jwt_identity

clothing_bp = Blueprint('clothing', __name__) # これでBlueprintが定義済みになる

@clothing_bp.route('/api/clothes', methods=['POST'])
@jwt_required()
def add_cloth():
    session = get_db_session()
    try:
        current_user_id = get_jwt_identity()
        user_id = current_user_id

        data = request.json
        new_cloth = Cloth(
            user_id=user_id,
            name=data.get('name'),
            category=data.get('category'),
            color=data.get('color'),
            material=data.get('material'),
            season=data.get('season'),
            is_formal=data.get('is_formal', False),
            image_url=data.get('image_url'),
        )
        session.add(new_cloth)
        session.commit()
        return jsonify({"message": "Cloth added successfully", "cloth_id": new_cloth.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500


@clothing_bp.route('/api/clothes/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_clothes(user_id):
    session = get_db_session()
    try:
        current_user_id = get_jwt_identity()
        if current_user_id != str(user_id):
            return jsonify({"message": "Forbidden: You can only view your own clothes"}), 403

        clothes = session.query(Cloth).filter_by(user_id=user_id).all()
        return jsonify([
            {
                "id": c.id, "name": c.name, "category": c.category, "color": c.color,
                "material": c.material, "season": c.season, "is_formal": c.is_formal,
                "image_url": c.image_url
            } for c in clothes
        ]), 200
    except Exception as e:
        session.rollback()
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500