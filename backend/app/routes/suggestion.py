from flask import Blueprint, request, jsonify
from app.database import get_db_session
from app.models import Cloth, UserPreference, OutfitSuggestion, User
from app.utils import generate_outfit_queries_with_openai, get_weather_info, embed_text
from flask_jwt_extended import jwt_required, get_jwt_identity

suggestion_bp = Blueprint('suggestion', __name__)


@suggestion_bp.route('/api/suggest_outfits', methods=['POST'])
@jwt_required()
def suggest_outfits():
    session = get_db_session()
    try:
        user_id = get_jwt_identity()

        data = request.json
        target_date = data.get('date')
        occasion = data.get('occasion') # 例: '仕事', 'カジュアル', 'デート'
        location = data.get('location', 'Kyoto, Japan') # 例: 京都、東京など

        # 必須パラメータのバリデーション
        if not target_date or not occasion:
            return jsonify({"message": "日付と外出先は必須です。"}), 400

        # ユーザーの服と好みを取得
        user_clothes = session.query(Cloth).filter_by(user_id=user_id).all()
        user_pref = session.query(UserPreference).filter_by(user_id=user_id).first()

        if not user_clothes:
            return jsonify({"message": "No clothes registered for this user."}), 400

        # 外部情報取得 (天気API)
        weather_info = get_weather_info(location, target_date)
        current_temperature = weather_info.get('temperature')
        weather_condition = weather_info.get('condition')

        # LLMへのプロンプト生成
        # user_id をプロンプトに含める場合、トークンから取得したものが確実
        clothes_descriptions = [f"{c.name} ({c.color}, {c.category}, {'フォーマル' if c.is_formal else 'カジュアル'})" for c in user_clothes]
        user_pref_str = ""
        if user_pref:
            if user_pref.preferred_style: user_pref_str += f"Preferred style: {user_pref.preferred_style}. "
            if user_pref.personal_color: user_pref_str += f"Personal color: {user_pref.personal_color}. "
            if user_pref.body_shape: user_pref_str += f"Body shape: {user_pref.body_shape}. "
            if user_pref.disliked_colors: user_pref_str += f"Disliked colors: {user_pref.disliked_colors}. "
            if user_pref.disliked_styles: user_pref_str += f"Disliked styles: {user_pref.disliked_styles}. "

        prompt = f"Given the user (ID: {user_id}) has clothes: {'; '.join(clothes_descriptions)}. " \
                 f"For {target_date}, weather is {weather_condition} ({current_temperature}°C), " \
                 f"and occasion is '{occasion}'. " \
                 f"User preferences: {user_pref_str}. " \
                 f"Suggest 3 unique outfits. " \
                 f"Each outfit should consist of a top, a bottom, and an optional outer. " \
                 f"Provide the ID of the selected items from the user's available clothes, a brief reason for the combination, and one 'recommended product' with name, image_url, buy_link. " \
                 f"Ensure all selected item IDs exist in the user's wardrobe. " \
                 f"Output in strict JSON format as an array of outfit objects."

        llm_response_json = generate_outfit_queries_with_openai(prompt) # LLMからJSON形式で受け取る

        suggested_outfits_data = llm_response_json.get('outfits', [])
        saved_suggestions = []

        for outfit_data in suggested_outfits_data:
            # LLMが返したIDが実際にユーザーが持つ服のIDと一致するか、かつそのユーザーIDに紐づいているか確認
            top_cloth = next((c for c in user_clothes if c.id == outfit_data.get('top_id') and c.user_id == user_id), None)
            bottom_cloth = next((c for c in user_clothes if c.id == outfit_data.get('bottom_id') and c.user_id == user_id), None)
            outer_cloth = next((c for c in user_clothes if c.id == outfit_data.get('outer_id') and c.user_id == user_id), None)

            # 少なくともトップスとボトムスがあれば保存・提案 (LLMが有効なIDを返す保証がないため、ここで最終チェック)
            if top_cloth and bottom_cloth:
                new_suggestion = OutfitSuggestion(
                    user_id=user_id,
                    suggested_date=target_date,
                    top_id=top_cloth.id,
                    bottom_id=bottom_cloth.id,
                    outer_id=outer_cloth.id if outer_cloth else None,
                    weather_info=f"{weather_condition}, {current_temperature}°C",
                    occasion_info=occasion
                )
                session.add(new_suggestion)
                session.flush() # ID取得のため

                saved_suggestions.append({
                    "suggestion_id": new_suggestion.id,
                    "top": { "id": top_cloth.id, "name": top_cloth.name, "color": top_cloth.color, "image_url": top_cloth.image_url },
                    "bottom": { "id": bottom_cloth.id, "name": bottom_cloth.name, "color": bottom_cloth.color, "image_url": bottom_cloth.image_url },
                    "outer": { "id": outer_cloth.id, "name": outer_cloth.name, "color": outer_cloth.color, "image_url": outer_cloth.image_url } if outer_cloth else None,
                    "reason": outfit_data.get('reason'),
                    "recommended_product": outfit_data.get('recommended_product')
                })
        session.commit()
        return jsonify({"suggestions": saved_suggestions}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500


# ユーザー設定（パーソナルカラーなど）の更新API
@suggestion_bp.route('/api/user_preferences/<int:user_id>', methods=['GET', 'PUT']) # GETも追加
@jwt_required() # JWT保護
def user_preferences(user_id): # 関数名をuser_preferencesに変更し、GET/PUTを処理
    session = get_db_session() # セッションを取得
    try:
        # JWTから認証済みユーザーのIDを取得し、認可チェック
        current_user_id = get_jwt_identity()
        if current_user_id != user_id:
            return jsonify({"message": "Forbidden: You can only view/update your own preferences"}), 403

        preference = session.query(UserPreference).filter_by(user_id=user_id).first()

        if request.method == 'GET':
            if not preference:
                # 設定がない場合はデフォルトまたは空の状態で返す
                return jsonify({
                    "user_id": user_id,
                    "personal_color": None,
                    "body_shape": None,
                    "disliked_colors": None,
                    "disliked_styles": None
                }), 200
            else:
                return jsonify({
                    "user_id": preference.user_id,
                    "personal_color": preference.personal_color,
                    "body_shape": preference.body_shape,
                    "disliked_colors": preference.disliked_colors,
                    "disliked_styles": preference.disliked_styles
                }), 200

        elif request.method == 'PUT':
            if not preference:
                preference = UserPreference(user_id=user_id)
                session.add(preference)

            data = request.json
            if 'personal_color' in data: preference.personal_color = data['personal_color']
            if 'body_shape' in data: preference.body_shape = data['body_shape']
            if 'disliked_colors' in data: preference.disliked_colors = data['disliked_colors']
            if 'disliked_styles' in data: preference.disliked_styles = data['disliked_styles']

            session.commit()
            return jsonify({"message": "User preferences updated successfully"}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500