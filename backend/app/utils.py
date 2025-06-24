import requests
import os
import json
import os
import requests
from PIL import Image
from io import BytesIO
import time
import uuid
from loguru import logger

import torch
from transformers import CLIPModel, CLIPProcessor

from pinecone import Pinecone, ServerlessSpec

# 仮のLLM連携関数
def get_llm_response(prompt: str) -> dict:
    # ダミー応答 (開発用)
    logger.info(f"LLM PROMPT:\n{prompt}")
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
    logger.info(f"Fetching weather for {location} on {date}")
    return {"temperature": 25, "condition": "晴れ"} 

def embed_text(text: str) -> list:
    # ダミー応答 (開発用)
    logger.info(f"Embedding text: {text}")
    return [0.1] * 768 # 仮の768次元ベクトル

# ベクトルデータベース検索関数
def search_vector_db(query_vector: list, category: str = None, top_k: int = 5) -> list:
    logger.info(f"Searching vector DB for query: {query_vector[:5]}..., category: {category}")
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
    logger.info("--- 1. Initializing Services ---")
    logger.info(f"Using device: {DEVICE}")

    # Pineconeクライアントの初期化
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY environment variable not set")
    pc = Pinecone(api_key=api_key)

    # CLIPモデルとプロセッサのロード
    logger.info("Loading CLIP model and processor...")
    model = CLIPModel.from_pretrained(MODEL_NAME).to(DEVICE)
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    
    # Pineconeインデックスの作成または接続
    embedding_dim = model.config.projection_dim
    if INDEX_NAME not in pc.list_indexes().names():
        logger.info(f"Creating index '{INDEX_NAME}' with dimension {embedding_dim}...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=embedding_dim,
            metric="cosine",
            spec=ServerlessSpec(cloud='aws', region='us-west-2')
        )
        logger.info("Index created successfully.")
    else:
        logger.info(f"Index '{INDEX_NAME}' already exists.")
        
    index = pc.Index(INDEX_NAME)
    logger.info(index.describe_index_stats())
    
    return model, processor, index



def embed_image(image: Image.Image, model: CLIPModel, processor: CLIPProcessor) -> list | None:
    """
    PIL.Image オブジェクトをCLIPモデルでベクトル化（エンべディング）する。

    Args:
        image (Image.Image): PILで開かれた画像オブジェクト
        model (CLIPModel): ロード済みのCLIPモデル
        processor (CLIPProcessor): ロード済みのCLIPプロセッサ

    Returns:
        list | None: 成功した場合はベクトルのリスト、失敗した場合はNone
    """
    try:
        # 画像をRGBに変換
        rgb_image = image.convert("RGB")
        inputs = processor(images=rgb_image, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            image_features = model.get_image_features(**inputs)
        return image_features[0].cpu().numpy().tolist()
    except Exception as e:
        logger.error(f"Failed to embed image: {e}")
        return None

# 既存の embed_image_from_url も、新しいヘルパー関数を使うように修正するとよりクリーンになります。
def embed_image_from_url(url: str, model: CLIPModel, processor: CLIPProcessor) -> list | None:
    """
    URLから画像を読み込み、CLIPモデルでベクトル化（エンべディング）する。
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        pil_image = Image.open(BytesIO(response.content))
        return embed_image(pil_image, model, processor) # 新しい関数を呼び出す
    except Exception as e:
        logger.error(f"Error processing image from URL {url}: {e}")
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
    logger.info("\n--- 2. Vectorizing and Upserting Images ---")
    vectors_to_upsert = []
    for item in image_data:
        embedding = embed_image_from_url(item["url"], model, processor)
        if embedding:
            vectors_to_upsert.append({
                "id": item["id"],
                "values": embedding,
                "metadata": {"description": item["description"], "url": item["url"]}
            })
        logger.info(f"Vectorized image: {item['id']}")

    if vectors_to_upsert:
        logger.info("\nUpserting vectors to Pinecone...")
        index.upsert(vectors=vectors_to_upsert)
        logger.info(f"Successfully upserted {len(vectors_to_upsert)} vectors.")

    logger.info("Waiting for indexing...")
    time.sleep(5)
    logger.info(index.describe_index_stats())

def upload_image_to_pinecone(
    image_bytes: bytes,
    user_id: str,
    item_metadata: dict,
    index: Pinecone.Index,
    model: CLIPModel,
    processor: CLIPProcessor
) -> dict:
    """
    フロントエンドから受け取った画像(bytes)をベクトル化し、Pineconeに登録する。

    Args:
        image_bytes (bytes): 画像ファイルのバイトデータ
        user_id (str): このアイテムを所有するユーザーのID (namespaceとして使用)
        item_metadata (dict): カテゴリや説明などの追加情報
        index (Pinecone.Index): Pineconeのインデックスオブジェクト
        model (CLIPModel): CLIPモデル
        processor (CLIPProcessor): CLIPプロセッサ

    Returns:
        dict: 処理結果
    """
    logger.info(f"Starting image upload for user: {user_id}")
    try:
        # バイトデータから画像を開く
        image = Image.open(BytesIO(image_bytes))

        # 画像をベクトル化
        image_vector = embed_image(image, model, processor)
        if not image_vector:
            return {"success": False, "error": "Failed to vectorize image."}

        # Pineconeに登録するデータを作成
        item_id = str(uuid.uuid4())  # 各アイテムに一意のIDを付与
        
        # 渡されたメタデータと必須項目を結合
        final_metadata = {
            "user_id": user_id,
            **item_metadata # categoryやdescriptionなど
        }

        vector_to_upsert = {
            "id": item_id,
            "values": image_vector,
            "metadata": final_metadata
        }

        # Pineconeにupsert (ユーザーIDをnamespaceとして使用)
        index.upsert(vectors=[vector_to_upsert], namespace=user_id)
        logger.success(f"Successfully uploaded item {item_id} for user {user_id} to namespace '{user_id}'.")

        return {
            "success": True,
            "item_id": item_id,
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"An unexpected error occurred during upload: {e}")
        return {"success": False, "error": str(e)}
    

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
    logger.info(f"\n--- Searching for: '{query}' ---")
    
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
        logger.info("No matches found.")
        return

    for match in result['matches']:
        logger.info(f"  ID: {match['id']}")
        logger.info(f"  Score: {match['score']:.4f}")
        logger.info(f"  Description: {match['metadata']['description']}")
        logger.info(f"  URL: {match['metadata']['url']}\n")


def main():
    """
    メインの処理フローを実行する。
    """
    # 1. サービスの初期化
    model, processor, index = initialize_services()

    # --- ★★★ 新しいアップロード関数のテスト (ここから) ★★★ ---
    logger.info("\n--- Testing new upload function ---")
    
    # テスト用の画像URLとメタデータ
    test_image_url = "https://www.khodaa-bloom.com/wp-content/uploads/RAIL-ST-F-mBK.jpg"
    test_user_id = "user-123"
    test_metadata = {
        "category": "bicycle",
        "color": "black",
        "description": "A cool and fast-looking black bicycle"
    }

    try:
        # URLから画像データをバイトとして取得
        response = requests.get(test_image_url)
        response.raise_for_status()
        image_as_bytes = response.content
        
        # 新しい関数を呼び出して画像をアップロード
        upload_result = upload_image_to_pinecone(
            image_bytes=image_as_bytes,
            user_id=test_user_id,
            item_metadata=test_metadata,
            index=index,
            model=model,
            processor=processor
        )
        logger.info(f"Upload result: {upload_result}")
    
    except Exception as e:
        logger.error(f"Failed to test upload function: {e}")
    
    # --- ★★★ (ここまで) ★★★ ---


    # ( ... 既存の検索処理などはそのまま ... )
    logger.info("\n--- Running original search queries ---")
    search_queries = [
        "an animal is resting",
        "a black bicycle"
    ]
    
    # user-123で検索する例
    # logger.info(f"--- Searching in user '{test_user_id}' namespace ---")
    # search_in_pinecone_with_namespace(...) # namespace付きの検索関数を別途作ると良い
    
    for query in search_queries:
        search_in_pinecone(query, index, model, processor) # これはデフォルトnamespaceを検索

if __name__ == "__main__":
    main()