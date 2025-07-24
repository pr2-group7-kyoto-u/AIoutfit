import os
import uuid
import json
import time
from io import BytesIO

import dotenv
import requests
import torch
import pycountry
from PIL import Image
from loguru import logger
from transformers import AutoModel, AutoProcessor
from pinecone import Pinecone, ServerlessSpec, exceptions
import openai

# -------------------------------------------------
#  Load environment variables
# -------------------------------------------------
dotenv.load_dotenv()

# -------------------------------------------------
#  Global constants
# -------------------------------------------------
MODEL_NAME = "openai/clip-vit-base-patch32"      # multilingual CLIP v2 (1024‑dim)
INDEX_NAME = "test"                          # Pinecone index name
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
EMBEDDING_DIM = 512                      # fixed for jina‑clip‑v2

# -------------------------------------------------
#  Service initialisation
# -------------------------------------------------

def initialize_services():
    """Initialise Pinecone, the CLIP model / processor and OpenAI client."""

    logger.info("--- Initialising services ---")
    logger.info(f"Using device: {DEVICE}")

    # --- Pinecone client ---
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_api_key:
        raise ValueError("PINECONE_API_KEY environment variable not set")
    pc = Pinecone(api_key=pinecone_api_key)

    # (Re)create a BYOV 1024‑dim index if necessary
    if INDEX_NAME not in pc.list_indexes().names():
        logger.info(f"Creating Pinecone index '{INDEX_NAME}' (dim={EMBEDDING_DIM}) …")
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        logger.info("Index created.")
    index = pc.Index(INDEX_NAME)
    logger.info(f"Index stats: {index.describe_index_stats()}")

    # --- OpenAI client ---
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    openai_client = openai.OpenAI(api_key=openai_api_key)

    # --- Model / processor ---
    model = AutoModel.from_pretrained(MODEL_NAME, trust_remote_code=True, torch_dtype=torch.float16, ).to(DEVICE)
    processor = AutoProcessor.from_pretrained(MODEL_NAME, trust_remote_code=True)

    return {
        "model": model,
        "processor": processor,
        "index": index,
        "openai_client": openai_client,
    }

# -------------------------------------------------
#  Embedding helpers
# -------------------------------------------------

def embed_image(image: Image.Image, model: AutoModel, processor: AutoProcessor):
    """Embed a PIL image into a 1024‑dim vector."""
    rgb = image.convert("RGB")
    inputs = processor(images=rgb, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        feats = model.get_image_features(**inputs)
    return feats[0].cpu().numpy().tolist()


def embed_text(text: str, model: AutoModel, processor: AutoProcessor):
    """Embed a text string into a 1024‑dim vector."""
    inputs = processor(text=[text], return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        feats = model.get_text_features(**inputs)
    return feats[0].cpu().numpy().tolist()

# -------------------------------------------------
#  Storage helpers
# -------------------------------------------------

def save_image_locally(image_bytes: bytes, user_id: str, item_id: str) -> str | None:
    """Save an image under static/uploads/{user_id}/{item_id}.jpg and return its URL path."""
    try:
        save_dir = os.path.join("static", "uploads", user_id)
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, f"{item_id}.jpg")
        with open(file_path, "wb") as fp:
            fp.write(image_bytes)
        url_path = os.path.join("uploads", user_id, f"{item_id}.jpg").replace(os.path.sep, "/")
        logger.success(f"Saved image → {file_path}")
        return f"/static/{url_path}"
    except Exception as e:
        logger.error(f"save_image_locally failed: {e}")
        return None


# -------------------------------------------------
#  Pinecone upsert / query
# -------------------------------------------------

def upload_image_to_pinecone(
    image_bytes: bytes,
    user_id: str,
    item_metadata: dict,
    services: dict,
):
    """Vectorise and upsert one image to Pinecone under the user's namespace."""
    model, processor, index = services["model"], services["processor"], services["index"]

    try:
        item_id = str(uuid.uuid4())
        image = Image.open(BytesIO(image_bytes))
        vector = embed_image(image, model, processor)
        if vector is None:
            return {"success": False, "error": "embedding failed"}

        image_url = save_image_locally(image_bytes, user_id, item_id)
        metadata = {"user_id": user_id, "image_url": image_url, **item_metadata}

        index.upsert(vectors=[{"id": item_id, "values": vector, "metadata": metadata}], namespace=user_id)
        return {"success": True, "item_id": item_id, "image_url": image_url}

    except Exception as e:
        logger.error(f"upload_image_to_pinecone error: {e}")
        return {"success": False, "error": str(e)}


def search_items_for_user(query: str, user_id: str, top_k: int, services: dict):
    model, processor, index = services["model"], services["processor"], services["index"]
    vector = embed_text(query, model, processor)
    res = index.query(vector=vector, top_k=top_k, include_metadata=True, namespace=user_id)
    return res.get("matches", [])

# -------------------------------------------------
#  LLM prompt helper
# -------------------------------------------------

def generate_outfit_queries(context: dict, services: dict):
    client = services["openai_client"]
    system_prompt = (
        "あなたは日本のトップファッションスタイリストです。"
        "提供されたユーザーの状況を分析し、最適な服装の組み合わせを1つ提案してください。\n"
        "回答は必ず以下のJSON形式で、キーも完全に一致させてください。\n"
        "{\"tops\": \"トップスの説明(英語)\", \"bottoms\": \"ボトムスの説明(英語)\", "
        "\"outerwear\": \"アウターの説明(英語、不要ならnull)\", \"shoes\": \"靴の説明(英語)\", "
        "\"reason\": \"このコーディネートを提案した理由(日本語)\"}"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
    )
    return json.loads(resp.choices[0].message.content)

# -------------------------------------------------
#  Main recommendation pipeline
# -------------------------------------------------

def get_outfit_recommendations(user_id: str, context: dict, services: dict, k: int = 3):
    idea = generate_outfit_queries(context, services)
    rec = {"reason": idea.get("reason"), "candidates": {}}
    for cat in ["tops", "bottoms", "outerwear", "shoes"]:
        query = idea.get(cat)
        if query:
            matches = search_items_for_user(query, user_id, k, services)
            rec["candidates"][cat] = matches
    return rec

# -------------------------------------------------
#  (Optional) Weather helpers – unchanged from your original
# -------------------------------------------------

def get_weather_info(location: str, days_from_now: int = 1):
    city, country = map(str.strip, location.split(","))
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        logger.warning("WEATHER_API_KEY not set")
        return {"temperature": None, "condition": "不明"}
    lat_lon = get_lat_and_lon(city, country)
    if not lat_lon:
        return {"temperature": None, "condition": "不明"}
    lat, lon = lat_lon
    url = (
        f"https://api.openweathermap.org/data/2.5/forecast/daily?lat={lat}&lon={lon}&cnt={days_from_now}"\
        f"&appid={api_key}"
    )
    try:
        data = requests.get(url, timeout=10).json()
        return data.get("list", [{}])[days_from_now - 1]
    except Exception:
        return {"temperature": None, "condition": "不明"}


def get_lat_and_lon(city: str, country: str):
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return None
    ref = pycountry.countries.get(name=country) or next(
        (c for c in pycountry.countries if country.lower() in c.name.lower()),
        None,
    )
    if not ref:
        return None
    url = f"https://api.openweathermap.org/geo/1.0/direct?q={city},{ref.alpha_2}&limit=1&appid={api_key}"
    try:
        data = requests.get(url, timeout=10).json()
        if data:
            return data[0]["lat"], data[0]["lon"]
    except Exception:
        pass
    return None

# -------------------------------------------------
#  Demo entry point (for quick sanity check)
# -------------------------------------------------

def main():
    services = initialize_services()

    # --- demo user & dummy upload
    user_id = "demo-user-001"
    # index = services["index"]
    # wipe namespace
    # try:
    #     index.delete(delete_all=True, namespace=user_id)
    # except exceptions.NotFoundException:
    #     logger.info(f"Namespace '{user_id}' not found → skip delete")

    sample = {
        "url": "https://m.media-amazon.com/images/I/51UHCwlXC7L._UY900_.jpg",
        "metadata": {"category": "top", "description": "formal white button‑down shirt", "color": "white"},
    }
    img_bytes = requests.get(sample["url"], timeout=15).content
    upload_image_to_pinecone(img_bytes, user_id, sample["metadata"], services)
    time.sleep(5)

    results = search_items_for_user("白シャツ", user_id, 5, services)
    logger.info("Search results for '白シャツ':")
    for m in results:
        logger.info(f"  score={m['score']:.3f} desc={m['metadata'].get('description')}")


if __name__ == "__main__":
    main()
