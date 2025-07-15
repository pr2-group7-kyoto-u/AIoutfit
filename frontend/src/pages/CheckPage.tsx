import React from 'react';
import { Link } from 'react-router-dom';
import styles from './normal.module.css';

//仮設定
const CheckPage: React.FC = () => (
  <div className={styles.normalBackground}>
    <h1>服確認</h1>
    <p>登録した服を確認できます。</p>
    <ul>
      <li><Link to="/">戻る</Link></li>
    </ul>
  </div>
);

export default CheckPage;