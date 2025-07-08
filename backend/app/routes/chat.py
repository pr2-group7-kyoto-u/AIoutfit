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
    AIに「提案」と「次の質問」を強制的に分離・生成させるためのシステムプロンプト。
    """
    return f"""
あなたは、ユーザーに最適な服装を提案する、非常に優秀なファッションアドバイザーです。
あなたのゴールは、対話を通じてユーザーの状況を完全に理解し、完璧なコーディネートを提案することです。

# あなたの最重要ルール
ユーザーから情報を受け取るたびに、以下の思考プロセスと出力形式を厳密に守ってください。
1.  **思考**: ユーザーの発言から得られた新しい情報（スロット）を更新する。次に聞くべき最も重要な情報は何かを考える。
2.  **出力**: 下記のJSON形式に従って、思考の結果を出力する。

# 出力形式 (必ずこのJSON形式で出力すること)
{{
  "text": "(コーデ提案を含む)ユーザーへの親しみやすいメッセージ",
  "next_question": "(次に聞くべき)ユーザーへの具体的な質問文",
  "suggestion_items": {{
      "tops": "提案するトップスのアイテム名",
      "bottoms": "提案するボトムスのアイテム名",
      "shoes": "提案する靴のアイテム名"
  }},
  "updated_slots": {{
      "date": "収集した日付情報 or null",
      "location_geo": "収集した地理情報 or null",
      "location_type": "収集した場所の性質 or null",
      "companion_age": "収集した相手の年齢 or null",
      "companion_gender": "収集した相手の性別 or null",
      "companion_style": "収集した相手の好み or null",
      "transport": "収集した移動手段 or null",
      "daily_plan": "収集した計画 or null"
  }},
  "type": "suggestion" | "final_suggestion"
}}

# 各フィールドの説明
- `text`: 提案の枕詞や感想などをここに記述します。コーデ提案の内容もここに含めてください。
- `next_question`: **必須項目。** コーデを洗練させるために、次に追加で聞きたい質問を一つだけ、ここに記述します。ユーザーが「確定」と言わない限り、必ず何か質問を入れてください。
- `suggestion_items`: **必須項目。** トップス、ボトムス、靴を必ず提案してください。ワンピース等はtopsとbottomsに同じ名前を入れてください。
- `type`: ユーザーが「確定」「それがいい」など明確な同意を示した場合のみ `"final_suggestion"` としてください。それ以外は常に `"suggestion"` です。

# 例
ユーザー発言: 「明日の夜、出かける予定です。」
あなたの出力:
{{
  "text": "明日の夜ですね、承知いたしました。夜は少し肌寒いかもしれませんので、長袖のブラウスにきれいめのパンツを合わせたスタイルはいかがでしょうか？",
  "next_question": "どちらへお出かけになりますか？",
  "suggestion_items": {{ "tops": "長袖のブラウス", "bottoms": "きれいめのパンツ", "shoes": "フラットシューズ" }},
  "updated_slots": {{ "date": "明日の夜", "location_geo": null, ... }},
  "type": "suggestion"
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