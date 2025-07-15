import React from 'react';
import { Link } from 'react-router-dom';
import styles from './normal.module.css';

//仮設定
const UploadPage: React.FC = () => (
  <div className={styles.normalBackground}>
    <h1>服登録</h1>
    <p>こちらで持っている服の登録ができます。</p>
    <ul>
      <li><Link to="/">戻る</Link></li>
    </ul>
  </div>
);

export default UploadPage;