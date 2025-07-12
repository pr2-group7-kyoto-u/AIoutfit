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

clothing_bp = Blueprint('clothing', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """許可された拡張子のファイルかチェックする"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@clothing_bp.route('/api/clothes', methods=['POST'])
@jwt_required()
def add_cloth():
    """
    服の情報を登録する。画像ファイルが添付されていれば、ユニークなファイル名を生成して
    MinIOにアップロードし、そのURLをDBに保存する。
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
                
                # ユニークなファイル名でMinIOにアップロード
                s3_client.upload_fileobj(
                    file,
                    s3_bucket,
                    unique_filename, # 変更点：ユニークなファイル名を使用
                    ExtraArgs={'ContentType': file.content_type}
                )
                
                # 公開URLもユニークなファイル名で生成
                image_url = f"/images/{unique_filename}"
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
        print(f"Error in add_cloth: {e}")
        return jsonify({"message": f"エラーが発生しました: {e}"}), 500


@clothing_bp.route('/api/clothes/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_clothes(user_id):
    # この関数は変更ありません
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
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
