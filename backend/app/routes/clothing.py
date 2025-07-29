import os
import uuid
import boto3
import openai
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
    clip_model, clip_processor, pinecone_index, _ = initialize_services()
    logger.info("clothing_bpでPineconeとCLIPサービスが初期化されました。")
except Exception as e:
    logger.error(f"clothing_bpでPineconeとCLIPサービスの初期化に失敗しました: {e}")
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
                image_url = f"{unique_filename}"
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
    """
    クエリに基づいて最適な服の組み合わせを検索する。
    1. 各カテゴリ（トップス、ボトムス、シューズ）でベクトル検索を実行し、候補を複数取得する。
    2. LLM（OpenAI API）を使い、候補の中からクエリに最も一致するアイテムを1つ選択させる。
    3. 最も一致したアイテムをカテゴリごとに返す。
    """
    data = request.get_json()
    if not data:
        return jsonify({"message": "リクエストボディが空です"}), 400

    current_user_id = get_jwt_identity()
    
    # OpenAIクライアントの初期化
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("OPENAI_API_KEY環境変数が設定されていません。")
            return jsonify({"message": "サーバーエラー: OpenAI APIキーが設定されていません"}), 500
        openai_client = openai.OpenAI(api_key=openai_api_key)
    except Exception as e:
        logger.error(f"OpenAIクライアントの初期化に失敗しました: {e}")
        return jsonify({"message": f"サーバーエラー: {e}"}), 500

    best_matches = {}
    # 'tops', 'bottoms', 'shoes' の各カテゴリに対して処理を実行
    for category in ['tops', 'bottoms', 'shoes']:
        query = data.get(category)
        if not query:
            continue

        # 1. Pineconeでベクトル検索を実行し、候補を取得 (top_k=3)
        try:
            search_results = search_items_for_user(
                query=query,
                user_id=current_user_id,
                index=pinecone_index,
                model=clip_model,
                processor=clip_processor,
                top_k=5,  # LLMに評価させるため、複数の候補を取得
                category=category
            )
            logger.info(search_results)

            if not search_results:
                best_matches[category] = None
                continue

        except Exception as e:
            logger.error(f"'{category}'のベクトル検索中にエラーが発生しました: {e}")
            best_matches[category] = {"error": "検索中にエラーが発生しました"}
            continue

        # 2. LLMに最も一致するアイテムを選択させる
        try:
            # LLMへの入力（プロンプト）を作成
            candidates_for_prompt = []
            for i, item in enumerate(search_results):
                # search_items_for_userが返すitemオブジェクトに 'id' が含まれている必要があります
                item_id = item.get('id') 
                meta = item.get('metadata', {})
                candidates_for_prompt.append(
                    f"候補{i+1} (ID: {item_id}):\n"
                    f"  - 説明: {meta.get('description', '説明なし')}\n"
                )
            
            prompt_text = (
                f"あなたはプロのスタイリストです。ユーザーの要望に最も合う服を、以下の候補リストから1つだけ選んでください。\n\n"
                f"## ユーザーの要望\n"
                f"「{query}」\n\n"
                f"## 服の候補リスト\n"
                f"{''.join(candidates_for_prompt)}\n"
                f"-----\n\n"
                f"## あなたのタスク\n"
                f"上記リストの中から最も要望に合う服の「ID」を一つだけ選び、そのIDの文字列を**完全にコピーして**回答してください。"
                f"説明やID以外の言葉は一切含めないでください。"
            )
            logger.info(f"LLMへのプロンプト: {prompt_text}")

            # OpenAI APIを呼び出し
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # または "gpt-4" など高性能なモデルを推奨
                messages=[{"role": "user", "content": prompt_text}],
                max_tokens=60, # IDのみを返すため、トークン数は少なく設定
                temperature=0, # 再現性を高めるために0に設定
            )
            logger.info(f"LLMの応答: {response.choices[0].message.content.strip()}")
            
            best_item_id = response.choices[0].message.content.strip()
            logger.success(f"LLMが選択したID ({category}): {best_item_id}")

            # 3. 選択されたIDを元に、元の検索結果から完全な情報を取得
            best_item = next((item for item in search_results if item.get('id') == best_item_id), None)

            # LLMがIDを正しく返さなかった場合のフォールバックとして、ベクトル検索のスコアが最も高いものを採用
            if not best_item:
                logger.warning(f"LLMが返したID '{best_item_id}' が候補に存在しません。ベクトル検索の最上位の結果を返します。")
                best_item = search_results[0]
            
            # フロントエンドに返す情報を整形
            best_matches[category] = [{
                'image_url': best_item['metadata'].get('image_url'),
                'score': best_item['score'],
                'metadata': best_item['metadata']
            }]

        except Exception as e:
            logger.error(f"OpenAI APIの呼び出し中にエラーが発生しました: {e}")
            # エラーが発生した場合は、ベクトル検索の最上位の結果をフォールバックとして返す
            best_item = search_results[0]
            best_matches[category] = [{
                'image_url': best_item['metadata'].get('image_url'),
                'score': best_item['score'],
                'metadata': best_item['metadata'],
                'error': 'LLMによる評価中にエラーが発生しました。'
            }]

    return jsonify(best_matches), 200
@clothing_bp.route('/api/clothes/<int:user_id>/<int:clothes_id>', methods=['DELETE'])
@jwt_required()
def delete_user_clothes(user_id, clothes_id):
    session = get_db_session()
    try:
        current_user_id = get_jwt_identity()
        if current_user_id != str(user_id):
            return jsonify({"message": "Forbidden: You can only delete your own clothes"}), 403

        deleted = session.query(Cloth).filter(Cloth.id == clothes_id, Cloth.user_id == user_id).delete(synchronize_session=False)
        if not deleted:
            return jsonify({"message": "Cloth not found"}), 404
        session.commit()
        return jsonify({"message": "Cloth deleted successfully", "cloth_id": clothes_id}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
    
@clothing_bp.route('/api/clothes/<int:user_id>/<int:clothes_id>', methods=['PATCH'])
@jwt_required()
def update_user_clothes(user_id, clothes_id):
    session = get_db_session()
    try:
        current_user_id = get_jwt_identity()
        if current_user_id != str(user_id):
            return jsonify({"message": "Forbidden: You can only update your own clothes"}), 403

        data = request.json

        session.query(Cloth).filter(Cloth.id == clothes_id, Cloth.user_id == user_id).update(data)
        session.commit()

        updated = session.query(Cloth).filter_by(id=clothes_id, user_id=user_id).first()
        return jsonify({
                "id": updated.id, "name": updated.name, "category": updated.category, "color": updated.color,
                "material": updated.material, "season": updated.season, "is_formal": updated.is_formal,
                "preferred": updated.preferred, "available": updated.available,
                "image_url": updated.image_url
            }), 200
    except Exception as e:
        session.rollback()
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
        
