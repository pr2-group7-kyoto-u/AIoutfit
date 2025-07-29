import React from 'react';
import { Link } from 'react-router-dom';
import styles from './normal.module.css';

//仮設定
const HistoryPage: React.FC = () => (
  <div className={styles.normalBackground}>
    <h1>履歴</h1>
    <p>こちらで過去に着たコーディネートを調べることができます。</p>
    <ul>
      <li><Link to="/home">戻る</Link></li>
    </ul>
  </div>
);

export default HistoryPage;