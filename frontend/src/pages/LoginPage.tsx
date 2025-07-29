// src/pages/LoginPage.tsx
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import styles from './normal.module.css'; // normal.module.cssをインポート

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const { success, message: msg } = await login(username, password);
    setMessage(msg);
    if (success) {
      navigate('/home');
    }
  };

  return (
    <div className={styles.normalBackground}> {/* HomePageと同じ背景 */}
      <div className={styles.mainContentArea}> {/* HomePageと同じカード型コンテナ */}
        <h1>ログイン</h1> {/* h1要素を直接使用 */}
        <p>アカウントにログインしてください。</p> {/* p要素を直接使用 */}

        {message && (
          <p className={`${styles.messageArea} ${message.includes('失敗') ? styles.errorMessage : styles.successMessage}`}>
            {message}
          </p>
        )}

        <form onSubmit={handleSubmit} className={styles.formContent}> {/* 共通のフォームスタイル */}
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
          <button type="submit" className={`${styles.actionButton} ${styles.submitButton}`}>
            ログイン
          </button>
        </form>
        <div className={styles.backButtonArea}>
          <Link to="/" className={`${styles.actionButton} ${styles.backLink}`}>戻る</Link>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;