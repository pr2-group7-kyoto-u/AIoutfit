// src/pages/FrontPage.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import styles from './normal.module.css'; 

const FrontPage: React.FC = () => (
  <div className={styles.normalBackground}>
    {/* メインコンテンツエリアを新しいクラスで囲む */}
    <div className={styles.mainContentArea}> 
      <h1>AIoutfit</h1> {/* h1要素を直接使用 */}
      <p>あなたのコーディネートをサポートします！</p>
      <ul> {/* ul要素を直接使用 */}
        <li><Link to="/register">ユーザ登録</Link></li>
        <li><Link to="/login">ログイン</Link></li>
      </ul>
    </div> {/* .mainContentArea 閉じタグ */}
  </div>
);

export default FrontPage;