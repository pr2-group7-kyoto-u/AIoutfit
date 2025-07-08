import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth'; // ⬅️ useAuthをインポート

const RegisterPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const { register } = useAuth(); // ⬅️ useAuthからregister関数を取得
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // useAuthのregister関数を呼び出す
    const { success, message: msg } = await register(username, password);
    setMessage(msg);
    // 成功したらダッシュボードへ
    if (success) {
      setTimeout(() => navigate('/dashboard'), 1500);
    }
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
      <Link to="/login">ログインページへ</Link>
    </div>
  );
};

export default RegisterPage;