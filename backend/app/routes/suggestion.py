from flask import Blueprint, request, jsonify
from app.database import get_db_session
from app.models import Cloth, UserPreference, OutfitSuggestion, User
from app.utils import generate_outfit_queries_with_openai, get_weather_info, embed_text
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

suggestion_bp = Blueprint('suggestion', __name__)


@suggestion_bp.route('/api/suggest_outfits', methods=['POST'])
@jwt_required()
def suggest_outfits():
    session = get_db_session()
    try:
        user_id = int(get_jwt_identity()) # user_idを整数に

        data = request.json
        target_date_str = data.get('date') # 日付は文字列として受け取る
        occasion = data.get('occasion')
        location = data.get('location', 'Kyoto, Japan')

        if not target_date_str or not occasion:
            return jsonify({"message": "日付と外出先は必須です。"}), 400
        
        # 文字列からdateオブジェクトに変換
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()

        user_clothes = session.query(Cloth).filter_by(user_id=user_id, is_available=True).all() # 利用可能な服のみを対象に
        user_pref = session.query(UserPreference).filter_by(user_id=user_id).first()
        user_info = session.query(User).filter_by(id=user_id).first()

        if not user_clothes:
            return jsonify({"message": "利用可能な服が登録されていません。"}), 400

        # (プロンプト生成ロジックは変更なし)
        weather_info = get_weather_info(location, target_date_str)
        clothes_descriptions = [f"ID:{c.id}, Name:{c.name} ({c.color}, {c.category})" for c in user_clothes]
        user_pref_str = ""
        if user_pref:
            if user_pref.personal_color: user_pref_str += f"Personal color: {user_pref.personal_color}. "
            # ... 他の好み ...
        
        prompt = f"User (ID:{user_id}, Age:{user_info.age}, Gender:{user_info.gender}) has clothes: {'; '.join(clothes_descriptions)}. " \
                 f"For {target_date_str}, weather is {weather_info.get('condition')} ({weather_info.get('temperature')}°C), " \
                 f"and occasion is '{occasion}'. User preferences: {user_pref_str}. " \
                 f"Suggest 3 unique outfits. Each outfit must have a top and a bottom, and can have an outer and shoes. " \
                 f"Provide the exact IDs for each item from the user's clothes list. " \
                 f"Provide a reason for each combination. " \
                 f"Output in strict JSON format as an array of objects, where each object has keys: 'top_id', 'bottom_id', 'outer_id', 'shoes_id', and 'reason'."

        llm_response_json = generate_outfit_queries_with_openai(prompt) # LLMからの応答
        suggested_outfits_data = llm_response_json.get('outfits', [])
        saved_suggestions = []

        for outfit_data in suggested_outfits_data:
            top_cloth = next((c for c in user_clothes if c.id == outfit_data.get('top_id')), None)
            bottom_cloth = next((c for c in user_clothes if c.id == outfit_data.get('bottom_id')), None)
            shoes_cloth = next((c for c in user_clothes if c.id == outfit_data.get('shoes_id')), None)

            if top_cloth and bottom_cloth:
                # 新しいモデルに合わせて保存するフィールドを限定する
                new_suggestion = OutfitSuggestion(
                    user_id=user_id,
                    suggested_date=datetime.strptime(target_date_str, '%Y-%m-%d').date(),
                    top_id=top_cloth.id,
                    bottom_id=bottom_cloth.id,
                    shoes_id=shoes_cloth.id if shoes_cloth else None
                    # weather_info, reason などはモデルにないので保存しない
                )
                session.add(new_suggestion)
                session.flush()

                saved_suggestions.append({
                    "suggestion_id": new_suggestion.id,
                    "top": {"id": top_cloth.id, "name": top_cloth.name},
                    "bottom": {"id": bottom_cloth.id, "name": bottom_cloth.name},
                    "shoes": {"id": shoes_cloth.id, "name": shoes_cloth.name} if shoes_cloth else None,
                    # 提案理由はDBに保存されないが、レスポンスには含める
                    "reason": outfit_data.get('reason')
                })
        
        session.commit()
        return jsonify({"suggestions": saved_suggestions}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
    finally:
        session.close()

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
    

@suggestion_bp.route('/api/suggestions', methods=['GET'])
@jwt_required()
def get_past_suggestions():
    """過去のコーデ提案履歴を取得する"""
    session = get_db_session()
    try:
        user_id = get_jwt_identity()
        
        # ユーザーの過去の提案を日付の降順で取得
        suggestions = session.query(OutfitSuggestion).filter_by(user_id=user_id).order_by(OutfitSuggestion.suggested_date.desc()).all()
        
        results = []
        for s in suggestions:
            results.append({
                "suggestion_id": s.id,
                "suggested_date": s.suggested_date.isoformat(),
                "top": {"id": s.top.id, "name": s.top.name, "color": s.top.color, "image_url": s.top.image_url} if s.top else None,
                "bottom": {"id": s.bottom.id, "name": s.bottom.name, "color": s.bottom.color, "image_url": s.bottom.image_url} if s.bottom else None,
                "shoes": {"id": s.shoes.id, "name": s.shoes.name, "color": s.shoes.color, "image_url": s.shoes.image_url} if s.shoes else None,
            })
            
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
    finally:
        session.close()

@suggestion_bp.route('/api/suggestions', methods=['POST'])
@jwt_required()
def save_suggestion():
    """指定された服の組み合わせでコーデ提案をDBに保存する"""
    session = get_db_session()
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        # 必須パラメータのチェック
        suggested_date_str = data.get('suggested_date')
        top_id = data.get('top_id')
        bottom_id = data.get('bottom_id')

        if not all([suggested_date_str, top_id, bottom_id]):
            return jsonify({"message": "日付、トップス、ボトムスは必須です"}), 400

        # オプショナルなパラメータ
        shoes_id = data.get('shoes_id')
        
        # 日付文字列をdateオブジェクトに変換
        suggested_date = datetime.strptime(suggested_date_str, '%Y-%m-%d').date()
        
        # --- 所有者チェック（セキュリティのため）---
        # 指定された服IDが本当にこのユーザーのものであるかを確認
        cloth_ids = [i for i in [top_id, bottom_id, shoes_id] if i is not None]
        user_clothes_count = session.query(Cloth).filter(Cloth.user_id == user_id, Cloth.id.in_(cloth_ids)).count()
        if user_clothes_count != len(cloth_ids):
            return jsonify({"message": "指定された服の中に、あなたの所持品でないものが含まれています"}), 403
        
        # 新しいコーデ提案オブジェクトを作成
        new_suggestion = OutfitSuggestion(
            user_id=user_id,
            suggested_date=suggested_date,
            top_id=top_id,
            bottom_id=bottom_id,
            shoes_id=shoes_id
        )

        session.add(new_suggestion)
        session.commit()
        session.refresh(new_suggestion)

        return jsonify({
            "message": "コーデが履歴に正常に保存されました",
            "suggestion_id": new_suggestion.id
        }), 201

    except Exception as e:
        session.rollback()
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
    finally:
        session.close()