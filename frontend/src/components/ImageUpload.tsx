import React, { useState } from 'react';
import api from '../api';

interface ImageUploadProps {
  onUploadSuccess: (data: { image_url: string }) => void;
}

const ImageUpload: React.FC<ImageUploadProps> = ({ onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [message, setMessage] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage('ファイルを選択してください。');
      return;
    }

    setIsUploading(true);
    setMessage('アップロード中...');

    try {
      const result = await api.uploadImage(selectedFile);
      setMessage(result.message);
      onUploadSuccess(result); // 親コンポーネントに成功を通知
    } catch (error: any) {
      setMessage(error.message || 'アップロードに失敗しました。');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div>
      <input type="file" accept="image/*" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={!selectedFile || isUploading}>
        {isUploading ? 'アップロード中...' : 'アップロード'}
      </button>
      {message && <p>{message}</p>}
    </div>
  );
};

export default ImageUpload;