import os
import uuid
import boto3
from botocore.client import Config
from botocore.exceptions import NoCredentialsError
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import get_db_session
from app.models import Cloth

# Pinecone関連のユーティリティをインポート
from app.utils import initialize_services, upload_image_to_pinecone, search_items_for_user
from PIL import Image
from io import BytesIO
from loguru import logger # デバッグ用のロギングを有効にするため

clothing_bp = Blueprint('clothing', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# ブループリントが作成された際に一度Pineconeサービスを初期化する
# より大規模なアプリケーションでは、app.pyや専用のサービスレイヤーで初期化を検討してください
try:
    # 画像の埋め込みとPineconeへのアップロードには、インデックス、モデル、プロセッサーのみが必要
    # openai_clientは服の登録では直接使用されない
    clip_model, clip_processor, pinecone_index, _ = initialize_services()
    logger.info("clothing_bpでPineconeとCLIPサービスが初期化されました。")
except Exception as e:
    logger.error(f"clothing_bpでPineconeとCLIPサービスの初期化に失敗しました: {e}")
    # サービスが失敗した場合、画像の埋め込みを無効にするなど、適切にエラーを処理してください
    clip_model = None
    clip_processor = None
    pinecone_index = None

def allowed_file(filename):
    """許可された拡張子のファイルかチェックする"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@clothing_bp.route('/api/clothes', methods=['POST'])
@jwt_required()
def add_cloth():
    """
    服の情報を登録する。画像ファイルが添付されていれば、ユニークなファイル名を生成して
    MinIOにアップロードし、そのURLをDBに保存し、Pineconeにも画像ベクトルを登録する。
    """
    session = get_db_session()
    try:
        current_user_id = get_jwt_identity()

        name = request.form.get('name')
        category = request.form.get('category')
        color = request.form.get('color')
        material = request.form.get('material')
        season = request.form.get('season')
        is_formal = request.form.get('is_formal', 'false').lower() == 'true'

        if not name or not category:
            return jsonify({"message": "服の名前とカテゴリは必須です"}), 400

        image_url = None
        image_bytes = None
        
        if 'image' in request.files:
            file = request.files['image']
            
            if file and file.filename and allowed_file(file.filename):
                # 元のファイル名から拡張子を取得 (例: ".jpg")
                _, extension = os.path.splitext(file.filename)
                
                # UUIDを使ってユニークなファイル名を生成
                unique_filename = f"{uuid.uuid4()}{extension}"
                
                # MinIOへの接続情報を取得
                s3_endpoint = os.environ.get('S3_ENDPOINT_URL')
                s3_key = os.environ.get('S3_ACCESS_KEY')
                s3_secret = os.environ.get('S3_SECRET_KEY')
                s3_bucket = os.environ.get('S3_BUCKET_NAME')

                s3_client = boto3.client(
                    's3',
                    endpoint_url=s3_endpoint,
                    aws_access_key_id=s3_key,
                    aws_secret_access_key=s3_secret,
                    config=Config(signature_version='s3v4')
                )
                
                # ファイルの内容をメモリに読み込む
                image_bytes = file.read()
                file.seek(0) # upload_fileobjのためにファイルポインタを先頭に戻す

                # ユニークなファイル名でMinIOにアップロード
                s3_client.upload_fileobj(
                    BytesIO(image_bytes), # BytesIOを使用してメモリからアップロード
                    s3_bucket,
                    unique_filename,
                    ExtraArgs={'ContentType': file.content_type}
                )
                
                # 公開URLもユニークなファイル名で生成
                image_url = f"/images/{unique_filename}"
                logger.info(f"MinIOに画像をアップロードしました: {image_url}")

                # Pineconeへのアップロード処理
                if clip_model and clip_processor and pinecone_index and image_bytes:
                    item_metadata = {
                        "name": name,
                        "category": category,
                        "color": color,
                        "material": material if material else "unknown", # materialが空の場合は"unknown"を設定
                        "season": season if season else "unknown", # seasonが空の場合は"unknown"を設定
                        "is_formal": is_formal if is_formal is not None else False, # is_formalが空の場合はFalseを設定
                        "description": f"{color}の{material}製の{name} ({category})" # CLIP検索用の説明
                    }
                    pinecone_upload_result = upload_image_to_pinecone(
                        image_bytes=image_bytes,
                        user_id=current_user_id, # user_idを文字列で渡す
                        item_metadata=item_metadata,
                        index=pinecone_index,
                        model=clip_model,
                        processor=clip_processor,
                        image_url=image_url
                    )
                    if pinecone_upload_result.get("success"):
                        logger.success(f"項目ID {pinecone_upload_result.get('item_id')} の画像ベクトルがPineconeにアップロードされました")
                    else:
                        logger.error(f"Pineconeへの画像ベクトルのアップロードに失敗しました: {pinecone_upload_result.get('error')}")
                else:
                    logger.warning("Pineconeサービスが完全に初期化されていないか、画像データがありません。Pineconeへのアップロードをスキップします。")
        
        # Clothオブジェクトを作成
        new_cloth = Cloth(
            user_id=int(current_user_id),
            name=name,
            category=category,
            color=color,
            material=material,
            season=season,
            is_formal=is_formal,
            image_url=image_url
            # vectorフィールドはmodels.pyにあるが、Pineconeを使用するためDBには保存しない（またはPineconeのIDを保存する）
            # ここではvectorを直接DBに保存しないことを想定
        )

        session.add(new_cloth)
        session.commit()
        session.refresh(new_cloth) # DBから最新の状態を読み込む

        return jsonify({
            "message": "服が正常に追加されました", 
            "cloth": {
                "id": new_cloth.id,
                "name": new_cloth.name,
                "image_url": new_cloth.image_url
            }
        }), 201

    except Exception as e:
        session.rollback()
        logger.error(f"add_clothでエラーが発生しました: {e}")
        return jsonify({"message": f"エラーが発生しました: {e}"}), 500


@clothing_bp.route('/api/clothes/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_clothes(user_id):
    session = get_db_session()
    try:
        current_user_id = get_jwt_identity()
        if current_user_id != str(user_id):
            return jsonify({"message": "Forbidden: You can only view your own clothes"}), 403

        clothes = session.query(Cloth).filter_by(user_id=user_id).all()
        return jsonify([
            {
                "id": c.id, "name": c.name, "category": c.category, "color": c.color,
                "material": c.material, "season": c.season, "is_formal": c.is_formal,
                "image_url": c.image_url
            } for c in clothes
        ]), 200
    except Exception as e:
        session.rollback()
        logger.error(f"get_user_clothesでエラーが発生しました: {str(e)}")
        return jsonify({"message": f"エラーが発生しました: {str(e)}"}), 500
    
    
@clothing_bp.route('/api/search/outfit', methods=['POST'])
@jwt_required()
def search_outfit():
    data = request.get_json()
    current_user_id = get_jwt_identity()

    # Pinecone & CLIP を準備
    model, processor, index, _ = initialize_services()

    results = {}
    for key in ['tops', 'bottoms', 'shoes']:
        query = data.get(key)
        if query:
            matches = search_items_for_user(           # utils.py に実装済み
                query=query,
                user_id=current_user_id,
                index=index,
                model=model,
                processor=processor,
                top_k=3
            )       
            logger.info(f"検索結果 ({key}): {matches}")
            # 必要情報だけフロントへ
            results[key] = [
                {
                    'image_url': m['metadata'].get('image_url'),
                    'score': m['score'],
                    'metadata': m['metadata']
                } for m in matches
            ]
    return jsonify(results), 200