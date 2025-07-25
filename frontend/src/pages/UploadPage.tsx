// src/pages/UploadPage.tsx
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../hooks/useAuth'; // useAuthをインポート
import styles from './normal.module.css'; // normal.module.cssをインポート

const UploadPage: React.FC = () => {
  const { user } = useAuth(); // ユーザー情報を取得
  const navigate = useNavigate();

  const [message, setMessage] = useState(''); // メッセージ表示用

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
      {/* UploadPageでは、直接 .normalBackground の子要素としてコンテンツを配置し、
          フォーム自体に背景や影を適用する構造とします。
          HomePageとは異なるCSSクラスの適用パターンですが、既存のラベル名を維持する方針に沿います。 */}

      {/* タイトルと簡易説明はここに残します */}
      <h1 className={styles.normalBackground_h1}>服の登録</h1> {/* normalBackground h1 のスタイルを適用 */}
      <p className={styles.normalBackground_p}>こちらで持っている服の登録ができます。</p> {/* normalBackground p のスタイルを適用 */}

      {message && (
        <p className={`${styles.normalBackground_messageDisplay} ${message.includes('失敗') ? styles.normalBackground_errorMessage : styles.normalBackground_successMessage}`}>
          {message}
        </p>
      )}

      <form onSubmit={handleAddCloth} className={styles.normalBackground_uploadFormContainer}>
        <div className={styles.normalBackground_formGroup}>
          <label htmlFor="clothName" className={styles.normalBackground_formLabel}>服の名前 (必須):</label>
          <input 
            id="clothName"
            type="text" 
            placeholder="例: 半袖Tシャツ" 
            value={newClothName} 
            onChange={(e) => setNewClothName(e.target.value)} 
            required 
            className={styles.normalBackground_formInput}
          />
        </div>
        <div className={styles.normalBackground_formGroup}>
          <label htmlFor="clothCategory" className={styles.normalBackground_formLabel}>カテゴリ (必須):</label>
          <input 
            id="clothCategory"
            type="text" 
            placeholder="例: トップス, ボトムス, アウター" 
            value={newClothCategory} 
            onChange={(e) => setNewClothCategory(e.target.value)} 
            required 
            className={styles.normalBackground_formInput}
          />
        </div>
        <div className={styles.normalBackground_formGroup}>
          <label htmlFor="clothColor" className={styles.normalBackground_formLabel}>色 (任意):</label>
          <input 
            id="clothColor"
            type="text" 
            placeholder="例: 黒, 青" 
            value={newClothColor} 
            onChange={(e) => setNewClothColor(e.target.value)} 
            className={styles.normalBackground_formInput}
          />
        </div>
        
        <div className={styles.normalBackground_formGroup}>
          <label htmlFor="clothImage" className={styles.normalBackground_formLabel}>画像 (任意):</label>
          <input 
            id="clothImage"
            type="file" 
            accept="image/*" 
            onChange={(e) => setSelectedImageFile(e.target.files ? e.target.files[0] : null)} 
            className={styles.normalBackground_fileInput}
          />
          {selectedImageFile && <p className={styles.normalBackground_fileName}>選択中のファイル: {selectedImageFile.name}</p>}
        </div>

        <button type="submit" className={styles.normalBackground_submitButton}>
          この服を登録する
        </button>
      </form>

      {/* 戻るボタンをここに残します */}
      {/* ul li Link の構造を維持したい場合 */}
      <ul className={styles.normalBackground_ul}> {/* normalBackground ul のスタイルを適用 */}
        <li className={styles.normalBackground_li}> {/* normalBackground li のスタイルを適用 */}
          <Link to="/" className={styles.normalBackground_a}>戻る</Link> {/* normalBackground a のスタイルを適用 */}
        </li>
      </ul>
      {/* あるいは、シンプルにLinkタグを直接配置 */}
      {/* <div className={styles.normalBackground_backLinkWrapper}>
        <Link to="/dashboard" className={styles.normalBackground_backLink}>ダッシュボードに戻る</Link>
      </div> */}
    </div>
  );
};

export default UploadPage;