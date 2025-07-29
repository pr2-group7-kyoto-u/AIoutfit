// src/pages/RegisterPage.tsx
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import styles from './normal.module.css'; // normal.module.cssをインポート

const RegisterPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [message, setMessage] = useState('');
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const { success, message: msg } = await register(username, password, age, gender);
    setMessage(msg);
    if (success) {
      setTimeout(() => navigate('/dashboard'), 1500);
    } 
  }; // ここでhandleSubmit関数が閉じられています

  return (
    <div className={styles.normalBackground}> {/* HomePageと同じ背景 */}
      <div className={styles.mainContentArea}> {/* HomePageと同じカード型コンテナ */}
        <h1>新規登録</h1> {/* h1要素を直接使用 */}
        <p>アカウントを作成して始めましょう。</p> {/* p要素を直接使用 */}

        {message && (
          <p className={`${styles.messageArea} ${message.includes('失敗') ? styles.errorMessage : styles.successMessage}`}>
            {message}
          </p>
        )}

        <form onSubmit={handleSubmit} className={styles.formContent}> {/* UploadPageと同じフォームスタイル */}
          <div className={styles.formGroup}>
            <label htmlFor="username" className={styles.formLabel}>ユーザー名:</label>
            <input 
              id="username"
              type="text" 
              placeholder="ユーザー名" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)} 
              className={styles.formInput}
              required 
            />
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="password" className={styles.formLabel}>パスワード:</label>
            <input 
              id="password"
              type="password" 
              placeholder="パスワード" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              className={styles.formInput}
              required 
            />
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="age" className={styles.formLabel}>年齢:</label>
            <input 
              id="age"
              type="number" 
              placeholder="年齢" 
              value={age} 
              onChange={(e) => setAge(e.target.value)} 
              className={styles.formInput}
            />
          </div>
          <div className={styles.formGroup}>
            <label htmlFor="gender" className={styles.formLabel}>性別:</label>
            <select 
              id="gender"
              value={gender} 
              onChange={(e) => setGender(e.target.value)}
              className={styles.formSelect} /* selectに新しいクラスを適用 */
            >
              <option value="">性別を選択</option>
              <option value="男性">男性</option>
              <option value="女性">女性</option>
              <option value="その他">その他</option>
            </select>
          </div>
          <button type="submit" className={`${styles.actionButton} ${styles.submitButton}`}>
            登録
          </button>
        </form>
        <div className={styles.backButtonArea}>
          <Link to="/login" className={`${styles.actionButton} ${styles.backLink}`}>ログインページへ</Link>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;