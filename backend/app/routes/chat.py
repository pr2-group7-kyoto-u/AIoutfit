from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils import initialize_services

chat_bp = Blueprint('chat', __name__)

# サービスを初期化（グローバルまたはリクエストごと）
# ここでは簡単のためグローバルに初期化しますが、アプリケーションの設計に応じて変更してください。
try:
    model, processor, index, openai_client = initialize_services()
except Exception as e:
    print(f"サービス初期化エラー: {e}")
    openai_client = None


@chat_bp.route('/api/chat', methods=['POST'])
@jwt_required()
def chat_with_ai():
    if not openai_client:
        return jsonify({"message": "OpenAIクライアントが初期化されていません。"}), 503

    current_user_id = get_jwt_identity()
    data = request.json
    conversation_history = data.get('messages')

    if not conversation_history:
        return jsonify({"message": "メッセージ履歴は必須です。"}), 400

    try:
        messages_for_api = [
            {"role": "system", "content": "あなたは親しみやすいファッションアドバイザーです。ユーザーの直前の発言だけでなく、今までの会話の流れを考慮して、日本語で簡潔に答えてください。"}
        ]
        messages_for_api.extend(conversation_history)

        # 修正: messagesパラメータに加工したメッセージリストを渡す
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_for_api
        )
        reply = response.choices[0].message.content
        return jsonify({"reply": reply}), 200

    except Exception as e:
        print(f"Error during OpenAI API call: {e}")
        return jsonify({"message": "AIとの通信中にエラーが発生しました。"}), 500