import os
import boto3
from botocore.client import Config
from botocore.exceptions import NoCredentialsError
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_image():
    if 'image' not in request.files:
        return jsonify({"message": "リクエストに画像ファイルが含まれていません"}), 400
    
    file = request.files['image']

    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"message": "ファイルが選択されていないか、許可されていない形式です"}), 400

    filename = secure_filename(file.filename)
    
    # MinIOへの接続情報を環境変数から取得
    s3_endpoint = os.environ.get('S3_ENDPOINT_URL')
    s3_key = os.environ.get('S3_ACCESS_KEY')
    s3_secret = os.environ.get('S3_SECRET_KEY')
    s3_bucket = os.environ.get('S3_BUCKET_NAME')

    # Boto3 S3クライアントの初期化
    s3_client = boto3.client(
        's3',
        endpoint_url=s3_endpoint,
        aws_access_key_id=s3_key,
        aws_secret_access_key=s3_secret,
        config=Config(signature_version='s3v4')
    )

    try:
        # ファイルをMinIOにアップロード
        s3_client.upload_fileobj(
            file,
            s3_bucket,
            filename,
            ExtraArgs={'ContentType': file.content_type}
        )
        
        # MinIO上のファイルURLを生成
        # localhost:9000はdocker-composeで公開しているポート
        image_url = f"http://localhost:9000/{s3_bucket}/{filename}"
        
        return jsonify({"message": "画像が正常にアップロードされました", "image_url": image_url}), 201

    except NoCredentialsError:
        return jsonify({"message": "認証情報が見つかりません"}), 500
    except Exception as e:
        return jsonify({"message": f"ファイルのアップロード中にエラーが発生しました: {e}"}), 500