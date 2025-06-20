import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [userId, setUserId] = useState<number | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await api.login(username, password);
    setMessage(result.message);
    if (result.user_id) {
      setUserId(result.user_id);
      localStorage.setItem('user_id', result.user_id); // 簡易的なユーザーID保存
    }
  };

  return (
    <div>
      <h2>ログイン</h2>
      <form onSubmit={handleSubmit}>
        <input type="text" placeholder="ユーザー名" value={username} onChange={(e) => setUsername(e.target.value)} />
        <input type="password" placeholder="パスワード" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button type="submit">ログイン</button>
      </form>
      {message && <p>{message}</p>}
      {userId && <p>ログイン成功！ユーザーID: {userId}</p>}
      <Link to="/">ホームに戻る</Link>
    </div>
  );
};

export default LoginPage;