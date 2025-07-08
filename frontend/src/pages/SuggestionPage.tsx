import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../hooks/useAuth';
import api, { DialogueSlots, HistoryMessage } from '../api';
import { Link, useNavigate } from 'react-router-dom';

// AIからのレスポンスの型
interface AiResponse {
  type: 'suggestion' | 'final_suggestion';
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
  const [isLoading, setIsLoading] = useState(true); // 初期ロード中はtrue
  const chatEndRef = useRef<HTMLDivElement>(null);

  // チャット履歴の末尾に自動スクロール
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  // ページ読み込み時に最初の対話を開始
  useEffect(() => {
    handleResponse("コーデの相談を始めたいです。");
  }, []);

  const handleResponse = async (userMessage: string) => {
    setIsLoading(true);

    // ユーザーのメッセージを履歴に追加
    const newHistory = [...history, { role: 'user' as const, content: userMessage }];
    setHistory(newHistory);

    try {
      const res: AiResponse = await api.proposeOutfit(slots, newHistory, userMessage);
      
      // AIからの返答を履歴に追加（提案と質問が一体になっている）
      const aiMessageContent = `${res.text}\n\n**提案:**\n- ${res.suggestion_items?.join('\n- ')}`;
      setHistory(prev => [...prev, { role: 'assistant' as const, content: aiMessageContent }]);
      
      // 状態を更新
      setSlots(res.updated_slots);

      // 最終提案ならコーデ確認画面へ遷移
      if (res.type === 'final_suggestion') {
        // ここで確定情報をstateにセットして確認画面に渡すなどの処理を追加できる
        alert("コーディネートが確定しました！");
        navigate('/dashboard'); 
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

  const handleConfirm = () => {
    // ユーザーが確定ボタンを押したときの処理
    handleResponse("このコーディネートで確定します。");
  };

  return (
    <div>
      <h2>AIコーデ相談 (逐次提案モード)</h2>
      <div style={{ height: '500px', overflowY: 'scroll', border: '1px solid #ccc', padding: '10px', marginBottom: '10px' }}>
        {history.map((msg, index) => (
          <div key={index} style={{ textAlign: msg.role === 'user' ? 'right' : 'left', margin: '5px 0' }}>
            <div style={{ whiteSpace: 'pre-wrap', display: 'inline-block', padding: '8px 12px', borderRadius: '10px', backgroundColor: msg.role === 'user' ? '#dcf8c6' : '#f1f0f0' }}>
              <strong>{msg.role === 'user' ? (user?.username || 'You') : 'AI'}:</strong><br/>
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && <p style={{textAlign: 'center'}}>AIが考えています...</p>}
        <div ref={chatEndRef} />
      </div>

      <div style={{ border: '1px solid blue', padding: '10px', margin: '10px 0' }}>
        <h4>アクション</h4>
        <p>AIの提案でよければ「これで確定」、情報を追加して提案を更新したい場合は、下の入力欄からメッセージを送ってください。</p>
        <button onClick={handleConfirm} disabled={isLoading || history.length === 0}>
          このコーデで確定
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isLoading ? "AIが応答中です..." : "追加情報や要望を入力..."}
          style={{ width: '80%', padding: '10px' }}
          disabled={isLoading}
        />
        <button type="submit" style={{ padding: '10px' }} disabled={isLoading}>
          送信して提案を更新
        </button>
      </form>
      <br/>
      <Link to="/dashboard">相談をやめる</Link>
    </div>
  );
};

export default SuggestionPage;