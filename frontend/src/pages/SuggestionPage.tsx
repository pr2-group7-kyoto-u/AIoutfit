import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../hooks/useAuth';
import api, { DialogueSlots, HistoryMessage } from '../api';
import { Link, useNavigate } from 'react-router-dom';

// AIからのレスポンスの型
interface AiResponse {
  type: 'question' | 'suggestion' | 'final_suggestion';
  text: string;
  suggestion_items?: string[];
  updated_slots: DialogueSlots;
}

const SuggestionPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [history, setHistory] = useState<HistoryMessage[]>([]);
  const [slots, setSlots] = useState<DialogueSlots>({});
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentSuggestion, setCurrentSuggestion] = useState<string[] | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // チャット履歴の末尾に自動スクロール
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  // ページ読み込み時に最初の対話を開始
  useEffect(() => {
    handleResponse("こんにちは！今日のコーデ相談を始めましょう。");
  }, []);

  const handleResponse = async (userMessage: string) => {
    setIsLoading(true);
    setCurrentSuggestion(null);

    // ユーザーのメッセージを履歴に追加
    const newHistory = [...history, { role: 'user' as const, content: userMessage }];
    setHistory(newHistory);

    try {
      const res: AiResponse = await api.proposeOutfit(slots, newHistory, userMessage);
      
      // AIからの返答を履歴に追加
      setHistory(prev => [...prev, { role: 'assistant' as const, content: res.text }]);
      // 状態を更新
      setSlots(res.updated_slots);

      if (res.type === 'suggestion' || res.type === 'final_suggestion') {
        setCurrentSuggestion(res.suggestion_items || []);
      }
    } catch (error: any) {
      const errorMessage = error.message || 'エラーが発生しました。';
      setHistory(prev => [...prev, { role: 'assistant' as const, content: errorMessage }]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    handleResponse(input);
    setInput('');
  };

  return (
    <div>
      <h2>AIコーデ相談</h2>
      <div style={{ height: '500px', overflowY: 'scroll', border: '1px solid #ccc', padding: '10px', marginBottom: '10px' }}>
        {history.map((msg, index) => (
          <div key={index} style={{ textAlign: msg.role === 'user' ? 'right' : 'left', margin: '5px 0' }}>
            <div style={{ display: 'inline-block', padding: '8px 12px', borderRadius: '10px', backgroundColor: msg.role === 'user' ? '#dcf8c6' : '#f1f0f0' }}>
              <strong>{msg.role === 'user' ? (user?.username || 'You') : 'AI'}:</strong> {msg.content}
            </div>
          </div>
        ))}
        {isLoading && <p>AIが考えています...</p>}
        <div ref={chatEndRef} />
      </div>

      {currentSuggestion && !isLoading && (
        <div style={{ border: '1px solid blue', padding: '10px', margin: '10px 0' }}>
          <h4>コーデ提案</h4>
          <ul>
            {currentSuggestion.map((item, i) => <li key={i}>{item}</li>)}
          </ul>
          <button onClick={() => navigate('/dashboard')}>これで確定！</button>
          <button onClick={() => handleResponse('いいえ、他の提案をお願いします')}>他の提案がいい</button>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isLoading ? "入力できません" : "メッセージを入力..."}
          style={{ width: '80%', padding: '10px' }}
          disabled={isLoading}
        />
        <button type="submit" style={{ padding: '10px' }} disabled={isLoading}>送信</button>
      </form>
      <br/>
      <Link to="/dashboard">相談をやめる</Link>
    </div>
  );
};

export default SuggestionPage;