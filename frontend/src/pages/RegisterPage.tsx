import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';

const RegisterPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await api.register(username, password);
    setMessage(result.message);
  };

  return (
    <div>
      <h2>新規登録</h2>
      <form onSubmit={handleSubmit}>
        <input type="text" placeholder="ユーザー名" value={username} onChange={(e) => setUsername(e.target.value)} />
        <input type="password" placeholder="パスワード" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button type="submit">登録</button>
      </form>
      {message && <p>{message}</p>}
      <Link to="/">ホームに戻る</Link>
    </div>
  );
};

export default RegisterPage;