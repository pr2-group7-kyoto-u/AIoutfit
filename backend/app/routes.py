from flask import request, jsonify
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

from .utils import get_weather_info, get_llm_response, embed_text
from .models import User, Cloth, OutfitSuggestion, UserPreference

def register_routes(app, Session):

    @app.route('/api/register', methods=['POST'])
    def register():
        session = Session()
        try:
            data = request.json
            username = data.get('username')
            password = data.get('password')
            if not username or not password:
                return jsonify({"message": "Username and password are required"}), 400

            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password_hash=hashed_password)
            session.add(new_user)
            session.commit()
            return jsonify({"message": "User registered successfully", "user_id": new_user.id}), 201
        except IntegrityError:
            session.rollback()
            return jsonify({"message": "Username already exists"}), 409
        except Exception as e:
            session.rollback()
            return jsonify({"message": f"An error occurred: {str(e)}"}), 500
        finally:
            session.close()

    @app.route('/api/login', methods=['POST'])
    def login():
        session = Session()
        try:
            data = request.json
            username = data.get('username')
            password = data.get('password')

            user = session.query(User).filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                return jsonify({"message": "Login successful", "user_id": user.id}), 200
            else:
                return jsonify({"message": "Invalid credentials"}), 401
        except Exception as e:
            return jsonify({"message": f"An error occurred: {str(e)}"}), 500
        finally:
            session.close()

    @app.route('/api/clothes', methods=['POST'])
    def add_cloth():
        session = Session()
        try:
            data = request.json
            # TODO: 認証済みのユーザーIDを取得
            user_id = data.get('user_id') # 仮にリクエストボディから取得
            if not user_id: return jsonify({"message": "Authentication required"}), 401



            new_cloth = Cloth(
                user_id=user_id,
                name=data.get('name'),
                category=data.get('category'),
                color=data.get('color'),
                material=data.get('material'),
                season=data.get('season'),
                is_formal=data.get('is_formal', False),
                image_url=data.get('image_url'),
                # vector=cloth_vector # ベクトルデータ
            )
            session.add(new_cloth)
            session.commit()
            return jsonify({"message": "Cloth added successfully", "cloth_id": new_cloth.id}), 201
        except Exception as e:
            session.rollback()
            return jsonify({"message": f"An error occurred: {str(e)}"}), 500
        finally:
            session.close()

    # ユーザーが持つ服の一覧取得
    @app.route('/api/clothes/<int:user_id>', methods=['GET'])
    def get_user_clothes(user_id):
        session = Session()
        try:
            clothes = session.query(Cloth).filter_by(user_id=user_id).all()
            return jsonify([
                {
                    "id": c.id, "name": c.name, "category": c.category, "color": c.color,
                    "material": c.material, "season": c.season, "is_formal": c.is_formal,
                    "image_url": c.image_url
                } for c in clothes
            ]), 200
        except Exception as e:
            return jsonify({"message": f"An error occurred: {str(e)}"}), 500
        finally:
            session.close()

    # コーデ提案
    @app.route('/api/suggest_outfits', methods=['POST'])
    def suggest_outfits():
        session = Session()
        try:
            data = request.json
            user_id = data.get('user_id')
            target_date = data.get('date')
            occasion = data.get('occasion') # 例: '仕事', 'カジュアル', 'デート'
            location = data.get('location', 'Kyoto, Japan') # 例: 京都、東京など

            # ユーザーの服と好みを取得
            user_clothes = session.query(Cloth).filter_by(user_id=user_id).all()
            user_pref = session.query(UserPreference).filter_by(user_id=user_id).first()

            if not user_clothes:
                return jsonify({"message": "No clothes registered for this user."}), 400

            # 外部情報取得
            weather_info = get_weather_info(location, target_date)
            current_temperature = weather_info.get('temperature')
            weather_condition = weather_info.get('condition')

            # LLMとの連携のダミー実装
            clothes_descriptions = [f"{c.name} ({c.color}, {c.category})" for c in user_clothes]
            prompt = f"Given the user has clothes: {', '.join(clothes_descriptions)}. " \
                     f"For {target_date}, weather is {weather_condition} ({current_temperature}°C), " \
                     f"and occasion is '{occasion}'. Suggest 3 outfits. " \
                     f"Provide item IDs, reasons, and one 'recommended product' with image_url/buy_link for each. " \
                     f"Output in JSON format."

            llm_response_json = get_llm_response(prompt) # LLMからJSON形式で受け取る
            # 例: llm_response_json = { "outfits": [ { "top_id": 1, "bottom_id": 2, "reason": "...", "recommended_product": { ... } } ] }

            suggested_outfits_data = llm_response_json.get('outfits', [])
            saved_suggestions = []

            for outfit_data in suggested_outfits_data:
                new_suggestion = OutfitSuggestion(
                    user_id=user_id,
                    suggested_date=target_date,
                    top_id=outfit_data.get('top_id'),
                    bottom_id=outfit_data.get('bottom_id'),
                    outer_id=outfit_data.get('outer_id'),
                    weather_info=f"{weather_condition}, {current_temperature}°C",
                    occasion_info=occasion
                )
                session.add(new_suggestion)
                session.flush() # ID取得のため

                saved_suggestions.append({
                    "suggestion_id": new_suggestion.id,
                    "top": next((c for c in user_clothes if c.id == outfit_data.get('top_id')), None),
                    "bottom": next((c for c in user_clothes if c.id == outfit_data.get('bottom_id')), None),
                    "outer": next((c for c in user_clothes if c.id == outfit_data.get('outer_id')), None),
                    "reason": outfit_data.get('reason'),
                    "recommended_product": outfit_data.get('recommended_product')
                })
            session.commit()
            return jsonify({"suggestions": saved_suggestions}), 200

        except Exception as e:
            session.rollback()
            return jsonify({"message": f"An error occurred: {str(e)}"}), 500
        finally:
            session.close()

    # ユーザー設定（パーソナルカラーなど）の更新
    @app.route('/api/user_preferences/<int:user_id>', methods=['PUT'])
    def update_user_preferences(user_id):
        session = Session()
        try:
            data = request.json
            preference = session.query(UserPreference).filter_by(user_id=user_id).first()
            if not preference:
                preference = UserPreference(user_id=user_id)
                session.add(preference)

            if 'personal_color' in data: preference.personal_color = data['personal_color']
            if 'body_shape' in data: preference.body_shape = data['body_shape']
            if 'disliked_colors' in data: preference.disliked_colors = data['disliked_colors']
            if 'disliked_styles' in data: preference.disliked_styles = data['disliked_styles']

            session.commit()
            return jsonify({"message": "User preferences updated successfully"}), 200
        except Exception as e:
            session.rollback()
            return jsonify({"message": f"An error occurred: {str(e)}"}), 500
        finally:
            session.close()