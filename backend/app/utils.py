import requests
import os
import json
import os
import requests
from PIL import Image
from io import BytesIO
import time

import torch
from transformers import CLIPModel, CLIPProcessor

from pinecone import Pinecone, ServerlessSpec

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


# --- グローバル設定 ---
MODEL_NAME = "openai/clip-vit-base-patch32"
INDEX_NAME = "test"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def initialize_services():
    """
    Pinecone、CLIPモデル、プロセッサを初期化し、インデックスに接続する。
    
    Returns:
        tuple: (model, processor, index) のタプル
    """
    print("--- 1. Initializing Services ---")
    print(f"Using device: {DEVICE}")

    # Pineconeクライアントの初期化
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY environment variable not set")
    pc = Pinecone(api_key=api_key)

    # CLIPモデルとプロセッサのロード
    print("Loading CLIP model and processor...")
    model = CLIPModel.from_pretrained(MODEL_NAME).to(DEVICE)
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    
    # Pineconeインデックスの作成または接続
    embedding_dim = model.config.projection_dim
    if INDEX_NAME not in pc.list_indexes().names():
        print(f"Creating index '{INDEX_NAME}' with dimension {embedding_dim}...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=embedding_dim,
            metric="cosine",
            spec=ServerlessSpec(cloud='aws', region='us-west-2')
        )
        print("Index created successfully.")
    else:
        print(f"Index '{INDEX_NAME}' already exists.")
        
    index = pc.Index(INDEX_NAME)
    print(index.describe_index_stats())
    
    return model, processor, index


def embed_image_from_url(url: str, model: CLIPModel, processor: CLIPProcessor) -> list | None:
    """
    URLから画像を読み込み、CLIPモデルでベクトル化（エンべディング）する。

    Args:
        url (str): 画像のURL
        model (CLIPModel): ロード済みのCLIPモデル
        processor (CLIPProcessor): ロード済みのCLIPプロセッサ

    Returns:
        list | None: 成功した場合はベクトルのリスト、失敗した場合はNone
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGB")
        
        inputs = processor(images=image, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            image_features = model.get_image_features(**inputs)
        
        return image_features[0].cpu().numpy().tolist()
    except Exception as e:
        print(f"Error processing image {url}: {e}")
        return None


def embed_text(text: str, model: CLIPModel, processor: CLIPProcessor) -> list:
    """
    テキストをCLIPモデルでベクトル化（エンべディング）する。

    Args:
        text (str): ベクトル化するテキスト
        model (CLIPModel): ロード済みのCLIPモデル
        processor (CLIPProcessor): ロード済みのCLIPプロセッサ

    Returns:
        list: ベクトルのリスト
    """
    inputs = processor(text=text, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        text_features = model.get_text_features(**inputs)
    return text_features[0].cpu().numpy().tolist()


def upsert_to_pinecone(index: Pinecone.Index, image_data: list, model: CLIPModel, processor: CLIPProcessor):
    """
    画像データをベクトル化し、Pineconeに登録（upsert）する。

    Args:
        index (Pinecone.Index): 接続済みのPineconeインデックス
        image_data (list): 登録する画像情報のリスト
        model (CLIPModel): ロード済みのCLIPモデル
        processor (CLIPProcessor): ロード済みのCLIPプロセッサ
    """
    print("\n--- 2. Vectorizing and Upserting Images ---")
    vectors_to_upsert = []
    for item in image_data:
        embedding = embed_image_from_url(item["url"], model, processor)
        if embedding:
            vectors_to_upsert.append({
                "id": item["id"],
                "values": embedding,
                "metadata": {"description": item["description"], "url": item["url"]}
            })
        print(f"Vectorized image: {item['id']}")

    if vectors_to_upsert:
        print("\nUpserting vectors to Pinecone...")
        index.upsert(vectors=vectors_to_upsert)
        print(f"Successfully upserted {len(vectors_to_upsert)} vectors.")

    print("Waiting for indexing...")
    time.sleep(5)
    print(index.describe_index_stats())


def search_in_pinecone(query: str, index: Pinecone.Index, model: CLIPModel, processor: CLIPProcessor, top_k: int = 3):
    """
    テキストクエリでPineconeを検索し、結果を表示する。

    Args:
        query (str): 検索するテキスト
        index (Pinecone.Index): 接続済みのPineconeインデックス
        model (CLIPModel): ロード済みのCLIPモデル
        processor (CLIPProcessor): ロード済みのCLIPプロセッサ
        top_k (int): 取得する検索結果の数
    """
    print(f"\n--- Searching for: '{query}' ---")
    
    # テキストをベクトル化
    query_vector = embed_text(query, model, processor)
    
    # Pineconeでクエリ実行
    result = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True
    )
    
    # 結果の表示
    if not result['matches']:
        print("No matches found.")
        return

    for match in result['matches']:
        print(f"  ID: {match['id']}")
        print(f"  Score: {match['score']:.4f}")
        print(f"  Description: {match['metadata']['description']}")
        print(f"  URL: {match['metadata']['url']}\n")


def main():
    """
    メインの処理フローを実行する。
    """
    # 1. サービスの初期化
    model, processor, index = initialize_services()

    # 2. 登録する画像データの定義
    image_data_to_register = [
        {"id": "img1", "url": "http://images.cocodataset.org/val2017/000000039769.jpg", "description": "A cat laying on a couch"},
        {"id": "img3", "url": "https://live.staticflickr.com/65535/52927351679_d502ea5087_b.jpg", "description": "A busy city street with cars and pedestrians"},
        {"id": "img4", "url": "https://newsatcl-pctr.c.yimg.jp/t/amd-img/20250301-00010018-ffield-000-1-view.jpg?exp=10800", "description": "A delicious looking pizza on a plate"},
        {"id": "img5", "url": "https://www.khodaa-bloom.com/wp-content/uploads/RAIL-ST-F-mBK.jpg", "description": "A beautiful black bicycle"},
    ]

    # 3. 画像をベクトル化してPineconeに登録
    upsert_to_pinecone(index, image_data_to_register, model, processor)

    # 4. テキストクエリで検索を実行
    search_queries = [
        "an animal is resting",
        "a black bicycle"
    ]
    
    for query in search_queries:
        search_in_pinecone(query, index, model, processor)


if __name__ == "__main__":
    main()