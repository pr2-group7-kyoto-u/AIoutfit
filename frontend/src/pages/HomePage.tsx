import React from 'react';
import { Link } from 'react-router-dom';
import styles from './normal.module.css';

const HomePage: React.FC = () => (
  <div className={styles.normalBackground}>
    <h1>ホームページ</h1>
    <p>目的のページへアクセスしてください。</p>
    <ul>
      <li><Link to="/uploadclothing">服を登録</Link></li>
      <li><Link to="/checkclothing">服を確認</Link></li>
      <li><Link to="/chatbot">服の提案を受ける</Link></li>
      <li><Link to="/history">履歴</Link></li>
      <li><Link to="/settings">設定</Link></li>
    </ul>
  </div>
);

export default HomePage;