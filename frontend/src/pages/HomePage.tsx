import React from 'react';
import { Link } from 'react-router-dom';

const HomePage: React.FC = () => (
  <div>
    <h1>毎日コーディネートアプリ</h1>
    <p>あなたの服から最適なコーディネートを提案します。</p>
    <ul>
      <li><Link to="/register">新規登録</Link></li>
      <li><Link to="/login">ログイン</Link></li>
      <li><Link to="/dashboard">ダッシュボード</Link> (ログイン後)</li>
    </ul>
  </div>
);

export default HomePage;