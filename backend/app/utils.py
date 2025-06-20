import requests
import os
import json

# 仮のLLM連携関数
def get_llm_response(prompt: str) -> dict:
    # ダミー応答 (開発用)
    print(f"LLM PROMPT:\n{prompt}")
    dummy_outfits = [
        {
            "top_id": 1, # 仮のID
            "bottom_id": 2, # 仮のID
            "outer_id": None,
            "reason": "今日の天候と外出先に合わせて、カジュアルながらも清潔感のある印象を与えます。",
            "recommended_product": {
                "name": "おしゃれなスニーカー",
                "image_url": "https://example.com/sneakers.jpg",
                "buy_link": "https://example.com/buy/sneakers"
            }
        },
        {
            "top_id": 3,
            "bottom_id": 4,
            "outer_id": 5,
            "reason": "少し肌寒い日のために、アウターを羽織ることで体温調節ができ、落ち着いた印象になります。",
            "recommended_product": {
                "name": "上質なウールマフラー",
                "image_url": "https://example.com/muffler.jpg",
                "buy_link": "https://example.com/buy/muffler"
            }
        },
        {
            "top_id": 1,
            "bottom_id": 4,
            "outer_id": None,
            "reason": "シンプルながらも色味を合わせた組み合わせで、普段使いに最適です。",
            "recommended_product": {
                "name": "シンプルなトートバッグ",
                "image_url": "https://example.com/bag.jpg",
                "buy_link": "https://example.com/buy/bag"
            }
        }
    ]
    return {"outfits": dummy_outfits}

def get_weather_info(location: str, date: str) -> dict:
    # ダミー応答 (開発用)
    print(f"Fetching weather for {location} on {date}")
    return {"temperature": 25, "condition": "晴れ"} 

def embed_text(text: str) -> list:
    # ダミー応答 (開発用)
    print(f"Embedding text: {text}")
    return [0.1] * 768 # 仮の768次元ベクトル

# ベクトルデータベース検索関数
def search_vector_db(query_vector: list, category: str = None, top_k: int = 5) -> list:
    print(f"Searching vector DB for query: {query_vector[:5]}..., category: {category}")
    # ダミー応答として、適当な服のIDを返す
    return [{"cloth_id": 1}, {"cloth_id": 2}] # 仮