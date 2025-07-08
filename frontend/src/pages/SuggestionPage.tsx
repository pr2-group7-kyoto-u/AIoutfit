import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../hooks/useAuth';
import api, { DialogueSlots, HistoryMessage } from '../api';
import { Link, useNavigate } from 'react-router-dom';

// 提案アイテムの型
interface SuggestionItems {
  tops: string;
  bottoms: string;
  shoes: string;
}

// AIからのレスポンスの型を更新
interface AiResponse {
  type: 'suggestion' | 'final_suggestion';
  text: string;
  next_question: string; // 質問を格納する専用フィールド
  suggestion_items?: SuggestionItems;
  updated_slots: DialogueSlots;
}

const SuggestionPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [history, setHistory] = useState<HistoryMessage[]>([]);
  const [slots, setSlots] = useState<DialogueSlots>({});
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [currentSuggestion, setCurrentSuggestion] = useState<SuggestionItems | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // チャット履歴の末尾に自動スクロール
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  // ページ読み込み時に最初の対話を開始
  useEffect(() => {
    // 初回メッセージをより自然なものに変更
    handleResponse("コーディネートの相談をお願いします。");
  }, []);

  const handleResponse = async (userMessage: string) => {
    setIsLoading(true);
    setCurrentSuggestion(null); // 新しい応答を待つ間、前の提案UIは非表示に

    const newHistory = [...history, { role: 'user' as const, content: userMessage }];
    setHistory(newHistory);

    try {
      const res: AiResponse = await api.proposeOutfit(slots, newHistory, userMessage);
      
      // AIの返答(提案＋質問)を組み立てて履歴に追加
      const aiMessageContent = `${res.text}\n\n**次の質問:**\n${res.next_question}`;
      setHistory(prev => [...prev, { role: 'assistant' as const, content: aiMessageContent }]);
      
      // 対話状態と提案アイテムを更新
      setSlots(res.updated_slots);
      if (res.suggestion_items) {
        setCurrentSuggestion(res.suggestion_items);
      }

      // AIが最終提案と判断した場合
      if (res.type === 'final_suggestion') {
        alert("コーディネートが確定しました！ダッシュボードに戻ります。");
        navigate('/dashboard'); 
      }
    } catch (error: any) {
      const errorMessage = error.message || 'エラーが発生しました。もう一度お試しください。';
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
    if (isLoading) return;
    handleResponse("このコーディネートで確定します。");
  };

  return (
    <div>
      <h2>AIコーデ相談 (全身提案モード)</h2>
      
      <div style={{ height: '500px', overflowY: 'scroll', border: '1px solid #ccc', padding: '10px', marginBottom: '10px' }}>
        {history.map((msg, index) => (
          <div key={index} style={{ textAlign: msg.role === 'user' ? 'right' : 'left', margin: '5px 0' }}>
            <div style={{ whiteSpace: 'pre-wrap', display: 'inline-block', padding: '8px 12px', borderRadius: '10px', backgroundColor: msg.role === 'user' ? '#dcf8c6' : '#f1f0f0' }}>
              <strong>{msg.role === 'user' ? (user?.username || 'You') : 'AIスタイリスト'}:</strong><br/>
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && <p style={{textAlign: 'center'}}>AIが考えています...</p>}
        <div ref={chatEndRef} />
      </div>

      {currentSuggestion && !isLoading && (
        <div style={{ border: '1px solid #007bff', padding: '10px', margin: '10px 0', borderRadius: '8px' }}>
          <h4>今回の提案コーデ</h4>
          <ul>
            {/* ワンピース判定 */}
            {currentSuggestion.tops === currentSuggestion.bottoms ? (
              <li><strong>Tops & Bottoms:</strong> {currentSuggestion.tops}</li>
            ) : (
              <>
                <li><strong>Tops:</strong> {currentSuggestion.tops}</li>
                <li><strong>Bottoms:</strong> {currentSuggestion.bottoms}</li>
              </>
            )}
            <li><strong>Shoes:</strong> {currentSuggestion.shoes}</li>
          </ul>
        </div>
      )}

      <div style={{ borderTop: '1px solid #ccc', paddingTop: '10px' }}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isLoading ? "AIが応答中です..." : "追加情報や要望を入力..."}
            style={{ flexGrow: 1, padding: '10px', borderRadius: '5px', border: '1px solid #ccc' }}
            disabled={isLoading}
          />
          <button type="submit" style={{ padding: '10px 15px', borderRadius: '5px', border: 'none', backgroundColor: '#28a745', color: 'white', cursor: 'pointer' }} disabled={isLoading}>
            送信して更新
          </button>
        </form>
        <button 
          onClick={handleConfirm} 
          disabled={isLoading || !currentSuggestion}
          style={{ width: '100%', padding: '10px', marginTop: '10px', borderRadius: '5px', border: 'none', backgroundColor: '#007bff', color: 'white', cursor: 'pointer' }}
        >
          このコーデで確定
        </button>
      </div>

      <div style={{ marginTop: '20px' }}>
        <Link to="/dashboard">相談をやめてダッシュボードに戻る</Link>
      </div>
    </div>
  );
};

export default SuggestionPage;