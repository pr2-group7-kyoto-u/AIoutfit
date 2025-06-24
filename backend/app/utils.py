import os
import uuid
import requests
from PIL import Image
from io import BytesIO
import time
from loguru import logger

import torch
from transformers import CLIPModel, CLIPProcessor
from pinecone import Pinecone, ServerlessSpec

# --- グローバル設定 ---
MODEL_NAME = "openai/clip-vit-base-patch32"
INDEX_NAME = "test"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# --- 外部連携の仮関数 (モック) ---
def get_llm_response(prompt: str) -> dict:
    """LLMからの応答を模倣するダミー関数"""
    logger.info(f"LLM PROMPT:\n{prompt}")
    # ... (この関数の実装は変更なし)
    return {}

def get_weather_info(location: str, date: str) -> dict:
    """天気情報APIの応答を模倣するダミー関数"""
    logger.info(f"Fetching weather for {location} on {date}")
    return {"temperature": 25, "condition": "晴れ"}

# --- サービス初期化 ---
def initialize_services():
    """Pinecone、CLIPモデル、プロセッサを初期化し、インデックスに接続する。"""
    logger.info("--- 1. Initializing Services ---")
    logger.info(f"Using device: {DEVICE}")
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY environment variable not set")
    pc = Pinecone(api_key=api_key)

    logger.info("Loading CLIP model and processor...")
    model = CLIPModel.from_pretrained(MODEL_NAME).to(DEVICE)
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    
    embedding_dim = model.config.projection_dim
    if INDEX_NAME not in pc.list_indexes().names():
        logger.info(f"Creating index '{INDEX_NAME}' with dimension {embedding_dim}...")
        pc.create_index(name=INDEX_NAME, dimension=embedding_dim, metric="cosine", spec=ServerlessSpec(cloud='aws', region='us-west-2'))
        logger.info("Index created successfully.")
    else:
        logger.info(f"Index '{INDEX_NAME}' already exists.")
        
    index = pc.Index(INDEX_NAME)
    logger.info(index.describe_index_stats())
    
    return model, processor, index

# --- 画像処理・ベクトル化 ---
def embed_image(image: Image.Image, model: CLIPModel, processor: CLIPProcessor) -> list | None:
    """PIL.Image オブジェクトをベクトル化する。"""
    try:
        rgb_image = image.convert("RGB")
        inputs = processor(images=rgb_image, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            image_features = model.get_image_features(**inputs)
        return image_features[0].cpu().numpy().tolist()
    except Exception as e:
        logger.error(f"Failed to embed image: {e}")
        return None

def embed_text(text: str, model: CLIPModel, processor: CLIPProcessor) -> list:
    """テキストをベクトル化する。"""
    inputs = processor(text=text, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        text_features = model.get_text_features(**inputs)
    return text_features[0].cpu().numpy().tolist()

# --- ファイル保存とDB操作 ---
def save_image_locally(image_bytes: bytes, user_id: str, item_id: str) -> str | None:
    """画像をローカルに保存し、URLパスを返す。"""
    try:
        save_dir = os.path.join('static', 'uploads', user_id, 'items')
        os.makedirs(save_dir, exist_ok=True)
        file_name = f"{item_id}.jpg"
        file_path = os.path.join(save_dir, file_name)
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        url_path = os.path.join('uploads', user_id, 'items', file_name).replace(os.path.sep, '/')
        logger.success(f"Successfully saved image locally to: {file_path}")
        return f"/static/{url_path}"
    except Exception as e:
        logger.error(f"Failed to save image locally: {e}")
        return None

def upload_image_to_pinecone(image_bytes: bytes, user_id: str, item_metadata: dict, index: Pinecone.Index, model: CLIPModel, processor: CLIPProcessor) -> dict:
    """画像をローカルに保存し、そのURLとベクトルをPineconeに登録する。"""
    logger.info(f"Starting image upload process for user: {user_id}")
    try:
        item_id = str(uuid.uuid4())
        image_url_path = save_image_locally(image_bytes, user_id, item_id)
        if not image_url_path:
            return {"success": False, "error": "Failed to save image locally."}
        
        image = Image.open(BytesIO(image_bytes))
        image_vector = embed_image(image, model, processor)
        if not image_vector:
            return {"success": False, "error": "Failed to vectorize image."}

        final_metadata = {"user_id": user_id, "image_url": image_url_path, **item_metadata}
        vector_to_upsert = {"id": item_id, "values": image_vector, "metadata": final_metadata}
        
        index.upsert(vectors=[vector_to_upsert], namespace=user_id)
        logger.success(f"Successfully processed and registered item {item_id} for user {user_id}.")

        return {"success": True, "item_id": item_id, "user_id": user_id, "image_url": image_url_path}
    except Exception as e:
        logger.error(f"An unexpected error occurred during upload process: {e}")
        return {"success": False, "error": str(e)}

# ★★★ 新しい検索関数 ★★★
def search_items_for_user(query: str, user_id: str, index: Pinecone.Index, model: CLIPModel, processor: CLIPProcessor, top_k: int = 3) -> list:
    """
    指定したユーザーのアイテムの中から、テキストクエリで検索する。

    Args:
        query (str): 検索するテキスト
        user_id (str): 検索対象のユーザーID (namespace)
        index (Pinecone.Index): Pineconeインデックス
        model (CLIPModel): CLIPモデル
        processor (CLIPProcessor): CLIPプロセッサ
        top_k (int): 取得する検索結果の数

    Returns:
        list: 検索結果のリスト
    """
    logger.info(f"\n--- Searching for: '{query}' in user '{user_id}' namespace ---")
    
    query_vector = embed_text(query, model, processor)
    
    result = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        namespace=user_id  # ★★★ ここでユーザーを指定 ★★★
    )
    
    matches = result.get('matches', [])
    if not matches:
        logger.warning("No matches found.")
    else:
        for match in matches:
            logger.info(f"  ID: {match['id']}")
            logger.info(f"  Score: {match['score']:.4f}")
            logger.info(f"  Metadata: {match['metadata']}\n")
            
    return matches

# --- メイン実行部分 ---
def main():
    """
    メインの処理フローを実行する。
    """
    # 1. サービスの初期化
    model, processor, index = initialize_services()

    # 2. テストユーザーとアイテム情報を定義
    test_user_id = "user-A789"
    items_to_upload = [
        {
            "url": "https://images.unsplash.com/photo-1598554747472-3567a54452b9?q=80&w=1964&auto=format&fit=crop",
            "metadata": {"category": "outer", "color": "beige", "description": "A light beige trench coat"}
        },
        {
            "url": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?q=80&w=1887&auto=format&fit=crop",
            "metadata": {"category": "bottom", "color": "blue", "description": "A pair of classic blue jeans"}
        },
        {
            "url": "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?q=80&w=1972&auto=format&fit=crop",
            "metadata": {"category": "top", "color": "white", "description": "A simple white t-shirt"}
        }
    ]

    # 3. 定義したアイテムをベクトル化してアップロード
    logger.info(f"\n--- Uploading items for user '{test_user_id}' ---")
    for item in items_to_upload:
        try:
            response = requests.get(item["url"])
            response.raise_for_status()
            upload_image_to_pinecone(
                image_bytes=response.content,
                user_id=test_user_id,
                item_metadata=item["metadata"],
                index=index,
                model=model,
                processor=processor
            )
        except Exception as e:
            logger.error(f"Failed to process and upload from {item['url']}: {e}")

    # 少し待ってインデックスの更新を反映させる
    logger.info("Waiting for indexing to settle...")
    time.sleep(10)
    
    # 4. アップロードしたユーザーのアイテムの中から検索
    search_queries = [
        "a simple white t-shirt",
        "classic blue jeans",
        "a beige coat for autumn"
    ]
    
    # ★修正箇所：forループでリストの各要素を一つずつ検索する
    for query in search_queries:
        search_items_for_user(
            query=query, # ループ変数 `query` (文字列) を渡す
            user_id=test_user_id,
            index=index,
            model=model,
            processor=processor,
            top_k=2
        )

if __name__ == "__main__":
    main()