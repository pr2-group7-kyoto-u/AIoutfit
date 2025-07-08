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

def create_iterative_system_prompt():
    """
    AIに「毎回提案＋毎回質問」を強制するためのシステムプロンプトを生成する。
    """
    return f"""
あなたは、ユーザーと対話しながらコーディネートを少しずつ洗練させていく、非常に優秀なファッションアドバイザーです。

# あなたの最重要ルール
ユーザーから新しい情報を一つ受け取るたびに、以下の2つを必ず実行してください。
1.  **暫定コーデの提示**: その時点で持っている全ての情報（不完全でも）を基に、最適なコーディネートを必ず提案する。
2.  **追加の質問**: コーデをより良くするために、次に必要な情報を一つだけ質問する。

# 対話の進め方
- ユーザーが「それで確定」「それがいい」のように同意の意思を示した場合のみ、`"type": "final_suggestion"`としてください。
- それ以外の場合は、ユーザーがどんな情報を追加しても、必ず暫定の提案と次の質問を続けてください。

# 出力形式 (必ずこのJSON形式で出力すること)
{{
  "type": "suggestion" | "final_suggestion",
  "text": "（提案の枕詞や次の質問など）ユーザーへの発言内容",
  "suggestion_items": ["提案するアイテム1", "提案するアイテム2", ...],
  "updated_slots": {{
    "date": "収集した日付情報 or null",
    "location_geo": "収集した地理情報 or null",
    "location_type": "収集した場所の性質 or null",
    "companion_age": "収集した相手の年齢 or null",
    "companion_gender": "収集した相手の性別 or null",
    "companion_style": "収集した相手の好み or null",
    "transport": "収集した移動手段 or null",
    "daily_plan": "収集した計画 or null"
  }}
}}

# 例
ユーザー発言: 「明日の夜、出かける予定です。」
あなたの出力:
{{
  "type": "suggestion",
  "text": "明日の夜ですね。承知いたしました。夜は少し肌寒いかもしれませんので、長袖のブラウスにきれいめのパンツを合わせたスタイルはいかがでしょうか？どちらへお出かけになりますか？",
  "suggestion_items": ["長袖のブラウス", "きれいめのパンツ"],
  "updated_slots": {{ "date": "明日の夜", "location_geo": null, ... }}
}}
"""

@chat_bp.route('/api/propose', methods=['POST'])
@jwt_required()
def propose_outfit():
    if not openai_client:
        return jsonify({"message": "OpenAIクライアントが初期化されていません。"}), 503

    data = request.json
    current_slots = data.get('slots', {})
    user_message = data.get('message')
    history = data.get('history', [])

    if not user_message:
        return jsonify({"message": "メッセージは必須です。"}), 400

    messages_for_api = [
        {"role": "system", "content": create_iterative_system_prompt()},
    ]
    # 過去の履歴をコンテキストに含める
    if history:
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
            response_format={"type": "json_object"}
        )
        ai_response_json = json.loads(response.choices[0].message.content)
        return jsonify(ai_response_json), 200

    except json.JSONDecodeError as e:
        print(f"JSONパースエラー: {e}\nレスポンス: {response.choices[0].message.content}")
        return jsonify({"message": "AIからの応答形式が正しくありません。"}), 500
    except Exception as e:
        print(f"提案の生成中にエラーが発生しました: {e}")
        return jsonify({"message": "提案の生成中にエラーが発生しました。"}), 500