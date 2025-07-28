// src/pages/HomePage.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import styles from './normal.module.css'; 

const HomePage: React.FC = () => (
  <div className={styles.normalBackground}>
    {/* メインコンテンツエリアを新しいクラスで囲む */}
    <div className={styles.mainContentArea}> 
      <h1>AIoutfit</h1> {/* h1要素を直接使用 */}
      <p>あなたのコーディネートをサポートします！</p>
      <p>目的のページへアクセスしてください。</p> {/* p要素を直接使用 */}
      <ul> {/* ul要素を直接使用 */}
        <li><Link to="/uploadclothing">服を登録</Link></li> {/* Linkはaタグとしてレンダリングされる */}
        <li><Link to="/checkclothing">服を確認</Link></li>
        <li><Link to="/suggest">服の提案を受ける</Link></li>
        <li><Link to="/history">履歴</Link></li>
        <li><Link to="/settings">設定</Link></li>
      </ul>
    </div> {/* .mainContentArea 閉じタグ */}
  </div>
);

export default HomePage;