import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import api, { Message } from '../api';
import { Link } from 'react-router-dom';



const ChatPage: React.FC = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [error, setError] = useState('');

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = { role: 'user', content: input };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');

    try {
      const response = await api.chatWithAI(newMessages);
      const assistantMessage: Message = { role: 'assistant', content: response.reply };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      setError(err.message || 'AIとの通信中にエラーが発生しました。');
      setMessages(messages)
    }
  };

  if (isLoading) {
    return <div>読み込み中...</div>;
  }

  if (!isAuthenticated) {
    return <div>このページにアクセスするには<Link to="/login">ログイン</Link>が必要です。</div>;
  }

  return (
    <div>
      <h2>AIチャット</h2>
      <p>AIスタイリストにファッションに関する質問をしてみましょう。</p>
      <div style={{ height: '400px', overflowY: 'scroll', border: '1px solid #ccc', padding: '10px', marginBottom: '10px' }}>
        {messages.map((msg, index) => (
          <div key={index} style={{ textAlign: msg.role === 'user' ? 'right' : 'left', margin: '5px 0' }}>
            <div style={{ display: 'inline-block', padding: '8px 12px', borderRadius: '10px', backgroundColor: msg.role === 'user' ? '#dcf8c6' : '#f1f0f0' }}>
              <strong>{msg.role === 'user' ? user?.username : 'AI'}:</strong> {msg.content}
            </div>
          </div>
        ))}
      </div>
      <form onSubmit={handleSendMessage}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="メッセージを入力..."
          style={{ width: '80%', padding: '10px' }}
        />
        <button type="submit" style={{ padding: '10px' }}>送信</button>
      </form>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <br />
      <Link to="/dashboard">ダッシュボードに戻る</Link>
    </div>
  );
};

export default ChatPage;