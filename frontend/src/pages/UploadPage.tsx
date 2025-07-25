// src/pages/UploadPage.tsx
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../hooks/useAuth';
import styles from './normal.module.css'; // normal.module.cssへのパスは './normal.module.css' で正しいです

// Cloth型はUploadPageでは直接使わないので削除してもOKですが、ここではそのまま残します
interface Cloth {
    id: number;
    name: string;
    color: string;
    category: string;
    image_url?: string;
}

const UploadPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [message, setMessage] = useState('');

  // 服登録フォーム用のstate
  const [newClothName, setNewClothName] = useState('');
  const [newClothCategory, setNewClothCategory] = useState('');
  const [newClothColor, setNewClothColor] = useState('');
  const [selectedImageFile, setSelectedImageFile] = useState<File | null>(null);

  // 服の追加処理
  const handleAddCloth = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      setMessage("ログインしていません。");
      return;
    }

    if (!newClothName || !newClothCategory) {
      setMessage("服の名前とカテゴリは必須です。");
      return;
    }

    try {
      const clothData = {
        name: newClothName,
        category: newClothCategory,
        color: newClothColor,
      };
      
      const result = await api.addCloth(clothData, selectedImageFile);

      setMessage(result.message);
      if (result.cloth) {
        // 成功したらフォームをリセット
        setNewClothName('');
        setNewClothCategory('');
        setNewClothColor('');
        setSelectedImageFile(null);
        // 必要に応じて、登録完了後にダッシュボードに戻るなどのナビゲーション
        // navigate('/dashboard'); 
      }
    } catch (error: any) {
      console.error("Failed to add cloth:", error);
      setMessage(error.message || "服の追加に失敗しました。");
    }
  };

  return (
    <div className={styles.normalBackground}> {/* 背景スタイルを適用 */}
      {/* メインコンテンツエリアを新しいクラスで囲む */}
      <div className={styles.mainContentArea}> 
        {/* h1とpは、mainContentAreaの直接の子なので、
            normal.module.cssの .mainContentArea h1 {} .mainContentArea p {} にスタイルが定義されていることを期待 */}
        <h1>服の登録</h1> 
        <p>こちらで持っている服の登録ができます。</p> 

        {/* メッセージ表示エリア */}
        {message && (
          <p className={`${styles.messageArea} ${message.includes('失敗') ? styles.errorMessage : styles.successMessage}`}>
            {message}
          </p>
        )}

        {/* 登録フォーム */}
        {/* formContentクラスを適用 */}
        <form onSubmit={handleAddCloth} className={styles.formContent}> 
          {/* 各フォームグループにformGroupクラスを適用 */}
          <div className={styles.formGroup}> 
            {/* ラベルにformLabelクラスを適用 */}
            <label htmlFor="clothName" className={styles.formLabel}>服の名前 (必須):</label> 
            {/* inputにformInputクラスを適用 */}
            <input 
              id="clothName"
              type="text" 
              placeholder="例: 半袖Tシャツ" 
              value={newClothName} 
              onChange={(e) => setNewClothName(e.target.value)} 
              required 
              className={styles.formInput} 
            />
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="clothCategory" className={styles.formLabel}>カテゴリ (必須):</label>
            <input 
              id="clothCategory"
              type="text" 
              placeholder="例: トップス, ボトムス, アウター" 
              value={newClothCategory} 
              onChange={(e) => setNewClothCategory(e.target.value)} 
              required 
              className={styles.formInput}
            />
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="clothColor" className={styles.formLabel}>色 (任意):</label>
            <input 
              id="clothColor"
              type="text" 
              placeholder="例: 黒, 青" 
              value={newClothColor} 
              onChange={(e) => setNewClothColor(e.target.value)} 
              className={styles.formInput}
            />
          </div>
          
          <div className={styles.formGroup}>
            <label htmlFor="clothImage" className={styles.formLabel}>画像 (任意): </label>
            {/* input type="file"にfileInputクラスを適用 */}
            <input 
              id="clothImage"
              type="file" 
              accept="image/*" 
              onChange={(e) => setSelectedImageFile(e.target.files ? e.target.files[0] : null)} 
              className={styles.fileInput} 
            />
            {selectedImageFile && <p className={styles.fileName}>選択中のファイル: {selectedImageFile.name}</p>}
          </div>

          {/* 「この服を登録する」ボタンに共通クラスと個別クラスを両方適用 */}
          <button type="submit" className={`${styles.actionButton} ${styles.submitButton}`}>
            この服を登録する
          </button>
        </form>

        {/* 戻るボタンエリアにbackButtonAreaクラスを適用 */}
        <div className={styles.backButtonArea}> 
          {/* Linkに共通クラスと個別クラスを両方適用 */}
          <Link to="/" className={`${styles.actionButton} ${styles.backLink}`}>戻る</Link>
        </div>
      </div> {/* .mainContentArea 閉じタグ */}
    </div>
  );
};

export default UploadPage;