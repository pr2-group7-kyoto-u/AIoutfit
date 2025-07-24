import os
import uuid
import pycountry
import requests
from PIL import Image
from io import BytesIO
import time
from loguru import logger
import openai
import json
import dotenv

import torch
from transformers import CLIPModel, CLIPProcessor
from pinecone import Pinecone, ServerlessSpec

# Load environment variables once at module level
dotenv.load_dotenv()

# --- グローバル設定 ---
MODEL_NAME = "openai/clip-vit-base-patch32"
INDEX_NAME = "test" # インデックス名をより具体的に変更
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# WEATHER_API_KEYは必要に応じてos.getenvで直接取得するか、引数として渡す

# --- サービス初期化 ---
def initialize_services():
    """Pinecone, CLIPモデル, OpenAIクライアント等を初期化する。"""
    logger.info("--- 1. Initializing Services ---")
    logger.info(f"Using device: {DEVICE}")

    # Pineconeクライアントの初期化
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp") # Changed default region to match spec
    
    if not pinecone_api_key:
        raise ValueError("PINECONE_API_KEY environment variable not set")
    pc = Pinecone(api_key=pinecone_api_key)

    # OpenAIクライアントの初期化
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    openai_client = openai.OpenAI(api_key=openai_api_key)
    logger.info("OpenAI client initialized.")
    
    # CLIPモデルとプロセッサのロード
    logger.info("Loading CLIP model and processor...")
    model = CLIPModel.from_pretrained(MODEL_NAME).to(DEVICE)
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    
    # Pineconeインデックスの作成または接続
    embedding_dim = model.config.projection_dim
    if INDEX_NAME not in pc.list_indexes().names():
        logger.info(f"Creating index '{INDEX_NAME}' with dimension {embedding_dim}...")
        pc.create_index(name=INDEX_NAME, dimension=embedding_dim, metric="cosine", spec=ServerlessSpec(cloud='aws', region='us-east-1'))
        logger.info("Index created successfully.")
    else:
        logger.info(f"Index '{INDEX_NAME}' already exists.")
        
    index = pc.Index(INDEX_NAME)
    logger.info(f"Initial index stats: {index.describe_index_stats()}")
    
    # 問題の行を削除: WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", WEATHER_API_KEY)

    return model, processor, index, openai_client

# --- 低レベルヘルパー関数 (ベクトル化・ファイル保存) ---
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

def save_image_locally(image_bytes: bytes, user_id: str, item_id: str) -> str | None:
    """画像をローカルに保存し、URLパスを返す。"""
    try:
        save_dir = os.path.join('static', 'uploads', user_id)
        os.makedirs(save_dir, exist_ok=True)
        file_name = f"{item_id}.jpg"
        file_path = os.path.join(save_dir, file_name)
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        url_path = os.path.join('uploads', user_id, file_name).replace(os.path.sep, '/')
        logger.success(f"Saved image locally to: {file_path}")
        return f"/static/{url_path}"
    except Exception as e:
        logger.error(f"Failed to save image locally: {e}")
        return None

# --- 中レベルコア関数 (DB操作) ---
def upload_image_to_pinecone(image_bytes: bytes, user_id: str, item_metadata: dict, index: Pinecone.Index, model: CLIPModel, processor: CLIPProcessor, image_url: str) -> dict:
    """画像をローカルに保存し、そのURLとベクトルをPineconeに登録する。"""
    logger.info(f"Starting image upload for user '{user_id}' with metadata: {item_metadata.get('description')}")
    try:
        item_id = str(uuid.uuid4())
        
        image = Image.open(BytesIO(image_bytes))
        image_vector = embed_image(image, model, processor)
        if not image_vector: return {"success": False, "error": "Failed to vectorize image."}

        final_metadata = {"user_id": user_id, "image_url": image_url, **item_metadata}
        vector_to_upsert = {"id": item_id, "values": image_vector, "metadata": final_metadata}
        
        index.upsert(vectors=[vector_to_upsert], namespace=user_id)
        return {"success": True, "item_id": item_id, "user_id": user_id, "image_url": image_url}
    except Exception as e:
        logger.error(f"An unexpected error occurred during upload process: {e}")
        return {"success": False, "error": str(e)}

def search_items_for_user(query: str, user_id: str, index: Pinecone.Index, model: CLIPModel, processor: CLIPProcessor, top_k: int, category:str) -> list:
    """指定したユーザーのアイテムの中から、テキストクエリで検索する。"""
    query_vector = embed_text(query, model, processor)
    logger.info(f"Searching for items for user '{user_id}' with query: '{query}'")
    result = index.query(
     vector=query_vector, 
     top_k=top_k, 
     include_metadata=True, 
     namespace=user_id,
     filter={"category": {"$eq": category}} )
    return result.get('matches', [])

# --- 高レベル "頭脳" 関数 (LLM連携) ---
def generate_outfit_queries_with_openai(context: dict, openai_client: openai.OpenAI) -> dict | None:
    """ユーザーの状況から、OpenAIモデルを使って最適な服装のクエリを生成する。"""
    logger.info("Generating outfit queries with OpenAI...")
    get_weather_info
    system_prompt = """
    あなたは日本のトップファッションスタイリストです。提供されたユーザーの状況を分析し、最適な服装の組み合わせを1つ提案してください。
    回答は必ず以下のJSON形式で、キーも完全に一致させてください。
    {"tops": "トップスの説明(英語)", "bottoms": "ボトムスの説明(英語)", "outerwear": "アウターの説明(英語、不要ならnull)", "shoes": "靴の説明(英語)", "reason": "このコーディネートを提案した理由(日本語)"}
    各服装の説明は、ベクトル検索で画像を見つけるため、色、素材、形、スタイル(例: casual, formal)など視覚的な特徴を具体的に記述してください。
    """
    user_prompt = f"以下のユーザー状況に最適な服装を提案してください。\n\n# ユーザーの状況\n{json.dumps(context, indent=2, ensure_ascii=False)}"
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        )
        outfit_queries = json.loads(response.choices[0].message.content)
        logger.success("Successfully generated outfit queries from OpenAI.")
        return outfit_queries
    except Exception as e:
        logger.error(f"Failed to call OpenAI API or parse response: {e}")
        return None

# --- 最上位アプリケーション関数 (全体統括) ---
def get_outfit_recommendations(user_id: str, context: dict, services: dict, top_k_per_category: int = 3) -> dict | None:
    """ユーザーの状況からLLMでクエリを生成し、ベクトル検索を実行して服装の候補を返す。"""
    logger.info(f"\n--- Starting outfit recommendation for user: {user_id} ---")
    outfit_idea = generate_outfit_queries_with_openai(context, services["openai_client"])
    if not outfit_idea: return None

    logger.info(f"LLM's Suggestion: {outfit_idea}")
    final_recommendation = {"reason": outfit_idea.get("reason"), "candidates": {}}

    for category in ["tops", "bottoms", "outerwear", "shoes"]:
        query = outfit_idea.get(category)
        if query:
            logger.info(f"--- Searching for '{category}' with query: '{query}' ---")
            search_results = search_items_for_user(
                query=query,
                user_id=user_id,
                top_k=top_k_per_category,
                # ★★★ 必要な引数だけを明示的に渡す ★★★
                index=services["index"],
                model=services["model"],
                processor=services["processor"]
            )
            final_recommendation["candidates"][category] = search_results

    logger.success("Outfit recommendation process completed.")
    return final_recommendation

# --- デモンストレーション実行 ---
def main():
    """メインの処理フローを実行する。"""
    services = { "model": None, "processor": None, "index": None, "openai_client": None }
    services["model"], services["processor"], services["index"], services["openai_client"] = initialize_services()

    # --- 1. テストデータのセットアップ ---
    test_user_id = "demo-user-001"
    logger.info(f"\n--- 1. Setting up test data for user '{test_user_id}' ---")
    
    # 既存のテストデータをクリーンアップ
    # try:
    #     services["index"].delete(delete_all=True, namespace=test_user_id)
    #     logger.warning(f"Cleared all previous data for namespace '{test_user_id}'.")
    #     time.sleep(5) # 削除が反映されるまで少し待つ
    # except Exception as e:
    #     logger.error(f"Could not clear namespace (it might be empty): {e}")

    items_to_upload = [
        {
        "image_url": "https://m.media-amazon.com/images/I/51UHCwlXC7L._UY900_.jpg",
        "metadata": {"category": "top", "description": "formal white button‑down shirt", "color": "white"},
        }
    ]
    for item in items_to_upload:
        try:
            response = requests.get(item["url"])
            response.raise_for_status()
            upload_image_to_pinecone(
                image_bytes=response.content,
                user_id=test_user_id,
                item_metadata=item["metadata"],
                # ★★★ 必要な引数だけを明示的に渡す ★★★
                index=services["index"],
                model=services["model"],
                processor=services["processor"]
            )
        except Exception as e:
            logger.error(f"Failed to process and upload from {item['url']}: {e}")
    
    time.sleep(10) # インデックスの更新を待つ
    logger.info(f"Setup complete. Current index stats: {services['index'].describe_index_stats()}")

    # --- 2. 服装提案の実行 ---
    user_context = {
        "schedule": "今夜、友人と京都のレストランでディナー",
        "weather": {"temperature": 22, "condition": "晴れ"},
        "preferences": "きれいめで、少しフォーマルなスタイルが良い。色はモノトーンが好き。",
        "gender": "男性"
    }
    
    recommendation = get_outfit_recommendations(
        user_id=test_user_id,
        context=user_context,
        services=services,
        top_k_per_category=2
    )

    # --- 3. 結果の表示 ---
    if recommendation:
        print("\n\n" + "="*50)
        logger.info("✨ AI Stylist's Final Recommendation ✨")
        print("="*50)
        logger.info(f"提案理由: {recommendation['reason']}")
        
        for category, items in recommendation['candidates'].items():
            if items:
                logger.info(f"\n--- Suggested {category.capitalize()} ---")
                for i, item in enumerate(items):
                    metadata = item['metadata']
                    logger.info(
                        f"  {i+1}. {metadata.get('description')} "
                        f"(Score: {item['score']:.4f}, URL: {metadata.get('image_url')})"
                    )
        print("\n" + "="*50)

def get_weather_info(location: str, days_from_now: int) -> dict:
    city = location.split(",")[0].strip()
    country = location.split(",")[1].strip()
    
    # Fetch API key directly here
    weather_api_key = os.getenv("WEATHER_API_KEY")
    if not weather_api_key:
        logger.error("WEATHER_API_KEY environment variable not set. Cannot fetch weather info.")
        return {"temperature": None, "condition": "不明"}

    coordinate = get_lat_and_lon(city, country) # Pass API key
    if not coordinate:
        logger.warning(f"Could not find coordinates for {location}.")
        return {"temperature": None, "condition": "不明"}
    lat = coordinate[0]
    lon = coordinate[1]

    api = f"https://api.openweathermap.org/data/2.5/forecast/daily?lat={lat}&lon={lon}&cnt={days_from_now}&appid={weather_api_key}"

    try:
        response = requests.get(api)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return {"temperature": None, "condition": "不明"}
    
    data = response.json()
    if not data or "list" not in data:
        print(f"No weather data found for {location}.")
        return {"temperature": None, "condition": "不明"}
    
    return data["list"][days_from_now - 1]

def get_lat_and_lon(city: str, country: str) -> tuple: # weather_api_key は関数内で取得するように修正されているはず
    # WEATHER_API_KEY を再度取得 (utils.py の initialize_services 修正でグローバル変数を参照するのではなく、直接 os.getenv で取得するように変更済み)
    weather_api_key = os.getenv("WEATHER_API_KEY")
    if not weather_api_key:
        logger.error("WEATHER_API_KEY environment variable not set. Cannot get coordinates.")
        return None

    country_iso = pycountry.countries.get(name=country)
    if not country_iso:
        matches = [c for c in pycountry.countries if country.lower() in c.name.lower()]
        country_iso = matches[0] if matches else None
    if not country_iso:
        logger.warning(f"Could not find ISO code for country: {country}")
        return None
    
    api = f"https://api.openweathermap.org/geo/1.0/direct?q={city},{country_iso.alpha_2}&limit=1&appid={weather_api_key}"
    
    try:
        response = requests.get(api)
        response.raise_for_status() # HTTPエラーレスポンス (4xx, 5xx) の場合に例外を発生させる
    except requests.RequestException as e:
        logger.error(f"位置情報取得中にエラーが発生しました: {city}, {country}. エラー: {e}")
        return None
    
    data = response.json()
    
    # data がリストであり、かつ空でないことを確認
    if not isinstance(data, list) or not data:
        logger.warning(f"'{city}, {country}' の座標が見つからないか、予期せぬAPI応答でした: {data}")
        return None
    
    return (data[0].get("lat"), data[0].get("lon"))

if __name__ == "__main__":
    main()