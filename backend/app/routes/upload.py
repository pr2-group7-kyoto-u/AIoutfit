import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

upload_bp = Blueprint('upload', __name__)

# 保存先のフォルダと許可する拡張子
UPLOAD_FOLDER = 'uploads' # app.pyからの相対パス
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_image():
    # リクエストにファイルパートがあるかチェック
    if 'image' not in request.files:
        return jsonify({"message": "リクエストに画像ファイルが含まれていません"}), 400
    
    file = request.files['image']

    # ファイル名が空でないかチェック
    if file.filename == '':
        return jsonify({"message": "ファイルが選択されていません"}), 400

    # ファイルが許可された拡張子かチェックし、保存
    if file and allowed_file(file.filename):
        # 安全なファイル名を生成
        filename = secure_filename(file.filename)
        # 保存パスを生成 (app.pyの場所を基準とする)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(save_path)
            # 成功したら、画像にアクセスするためのURLを返す
            image_url = f"/uploads/{filename}"
            return jsonify({"message": "画像が正常にアップロードされました", "image_url": image_url}), 201
        except Exception as e:
            return jsonify({"message": f"ファイルの保存中にエラーが発生しました: {e}"}), 500

    return jsonify({"message": "許可されていないファイル形式です"}), 400