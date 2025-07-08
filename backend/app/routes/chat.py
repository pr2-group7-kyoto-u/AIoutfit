from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.utils import initialize_services
import json

chat_bp = Blueprint('chat', __name__)

try:
    _, _, _, openai_client = initialize_services()
except Exception as e:
    print(f"サービス初期化エラー: {e}")
    openai_client = None

# AIが収集すべき情報のテンプレート
INFORMATION_SLOTS = {
    "date": None,
    "location_geo": None,
    "location_type": None,
    "companion_age": None,
    "companion_gender": None,
    "companion_style": None,
    "transport": None,
    "daily_plan": None,
}

def create_system_prompt():
    """AIに役割とルールを指示するためのプロンプトを生成する"""
    return f"""
あなたはユーザーに最適な服装を提案する、非常に優秀なファッションアドバイザーです。
以下のルールに従って、ユーザーとの対話を進めてください。

# ゴール
ユーザーとの対話を通じて、以下の情報をすべて聞き出し、完璧なコーディネートを提案すること。
- date: いつ（例：明日の夜、週末の昼）
- location_geo: どこで（例：京都駅、大阪のカフェ）
- location_type: 場所の性質（例：食事、ショッピング、デート）
- companion_age: 会う相手の年齢
- companion_gender: 会う相手の性別
- companion_style: 会う相手の服装や好み
- transport: 移動手段（例：電車、徒歩、車）
- daily_plan: 当日の具体的な計画（例：食事の後に映画を見る）

# 対話の進め方
1. 一度にたくさんの質問をせず、自然な会話の流れで一つか二つずつ重要な情報から聞いてください。
2. ある程度情報が集まったら（最低でも「いつ」「どこで」「誰と」）、一度コーディネートを提案してください。
3. ユーザーが提案を拒否した場合（「いいえ」「違う」など）、不足している情報を聞き出す質問をしてください。
4. ユーザーが提案に同意した場合、あるいはすべての情報が収集できたと判断した場合は、`"type": "final_suggestion"`として提案してください。

# 出力形式
あなたの返答は、必ず以下のJSON形式で出力してください。

{{
  "type": "question" | "suggestion" | "final_suggestion",
  "text": "ユーザーへの発言内容（自然な会話口調で）",
  "suggestion_items": ["トップス：白いブラウス", "ボトムス：黒いスカート", "靴：ローヒールパンプス"],
  "updated_slots": {{
    "date": "収集した日付情報 or null",
    "location_geo": "収集した地理情報 or null",
    ...（他のスロットも同様）
  }}
}}

- `type`: あなたのレスポンスの種類。`question`は追加質問、`suggestion`は中間提案、`final_suggestion`は最終提案。
- `text`: ユーザーに見せるメッセージ。
- `suggestion_items`: `suggestion`または`final_suggestion`の場合に、提案するアイテムのリストを含める。
- `updated_slots`: ユーザーの今回の発言内容を反映した、最新の情報スロットの状態。
"""

@chat_bp.route('/api/propose', methods=['POST'])
@jwt_required()
def propose_outfit():
    if not openai_client:
        return jsonify({"message": "OpenAIクライアントが初期化されていません。"}), 503

    data = request.json
    # フロントから現在の対話状態とユーザーの最新メッセージを受け取る
    current_slots = data.get('slots', INFORMATION_SLOTS.copy())
    user_message = data.get('message')
    history = data.get('history', [])

    if not user_message:
        return jsonify({"message": "メッセージは必須です。"}), 400

    messages_for_api = [
        {"role": "system", "content": create_system_prompt()},
    ]
    # 過去の履歴をコンテキストに含める
    messages_for_api.extend(history)
    # 最新のユーザーメッセージと現在の状態を伝える
    messages_for_api.append({
        "role": "user",
        "content": f"現在の情報：{current_slots}\n\nユーザーの発言：「{user_message}」"
    })

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_for_api,
            response_format={"type": "json_object"} # JSONモードを有効化
        )
        ai_response_json = json.loads(response.choices[0].message.content)
        return jsonify(ai_response_json), 200

    except json.JSONDecodeError as e:
        print(f"JSONパースエラー: {e}")
        print(f"OpenAIからの不正なレスポンス: {response.choices[0].message.content}")
        return jsonify({"message": "AIからの応答を解析できませんでした。"}), 500
    except Exception as e:
        print(f"提案の生成中にエラーが発生しました: {e}")
        return jsonify({"message": "提案の生成中にエラーが発生しました。"}), 500

