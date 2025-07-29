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
        navigate('/result', { state: { suggestion: res.suggestion_items } }); 
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

    navigate('/result', { state: { suggestion: currentSuggestion } });
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '20px auto', backgroundColor: '#fff', borderRadius: '10px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
      <h2 style={{ textAlign: 'center', marginBottom: '20px', color: '#333' }}>AIコーデ相談 (全身提案モード)</h2>
      
      <div style={{ height: '500px', overflowY: 'auto', border: '1px solid #eee', padding: '15px', marginBottom: '15px', borderRadius: '8px', backgroundColor: '#f9f9f9' }}>
        {history.map((msg, index) => (
          <div key={index} style={{ textAlign: msg.role === 'user' ? 'right' : 'left', margin: '10px 0' }}>
            <div style={{ 
                whiteSpace: 'pre-wrap', 
                display: 'inline-block', 
                padding: '10px 15px', 
                borderRadius: '18px', /* より丸く */
                backgroundColor: msg.role === 'user' ? '#DCF8C6' : '#E0E0E0', /* 色を調整 */
                maxWidth: '70%', /* 吹き出しの最大幅を制限 */
                boxShadow: '0 1px 2px rgba(0,0,0,0.1)' /* 軽い影 */
              }}>
              <strong style={{ color: msg.role === 'user' ? '#007bff' : '#333' }}>{msg.role === 'user' ? (user?.username || 'You') : 'AIスタイリスト'}:</strong><br/>
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && <p style={{textAlign: 'center', color: '#666'}}>AIが考えています...</p>}
        <div ref={chatEndRef} />
      </div>

      {currentSuggestion && !isLoading && (
        <div style={{ border: '1px solid #007bff', padding: '15px', margin: '15px 0', borderRadius: '10px', backgroundColor: '#eef7ff', boxShadow: '0 2px 5px rgba(0, 123, 255, 0.1)' }}>
          <h4 style={{ textAlign: 'center', marginBottom: '10px', color: '#007bff' }}>今回の提案コーデ</h4>
          <ul style={{ listStyle: 'none', padding: '0', margin: '0' }}>
            {/* ワンピース判定 */}
            {currentSuggestion.tops === currentSuggestion.bottoms ? (
              <li style={{ padding: '5px 0', borderBottom: '1px dotted #ccc' }}><strong>Tops & Bottoms:</strong> {currentSuggestion.tops}</li>
            ) : (
              <>
                <li style={{ padding: '5px 0', borderBottom: '1px dotted #ccc' }}><strong>Tops:</strong> {currentSuggestion.tops}</li>
                <li style={{ padding: '5px 0', borderBottom: '1px dotted #ccc' }}><strong>Bottoms:</strong> {currentSuggestion.bottoms}</li>
              </>
            )}
            <li style={{ padding: '5px 0' }}><strong>Shoes:</strong> {currentSuggestion.shoes}</li>
          </ul>
        </div>
      )}

      <div style={{ borderTop: '1px solid #eee', paddingTop: '15px' }}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isLoading ? "AIが応答中です..." : "追加情報や要望を入力..."}
            style={{ flexGrow: 1, padding: '12px', borderRadius: '25px', border: '1px solid #ddd', fontSize: '1em' }} /* 丸い入力欄 */
            disabled={isLoading}
          />
          <button type="submit" 
            style={{ 
              padding: '12px 20px', 
              borderRadius: '25px', /* 丸いボタン */
              border: 'none', 
              backgroundColor: '#28a745', 
              color: 'white', 
              cursor: 'pointer', 
              fontSize: '1em',
              fontWeight: 'bold',
              transition: 'background-color 0.2s ease',
              flexShrink: 0 /* 幅が縮まないように */
            }} 
            disabled={isLoading}>
            送信して更新
          </button>
        </form>
        <button 
          onClick={handleConfirm} 
          disabled={isLoading || !currentSuggestion}
          // ★幅の修正: width: 'auto'または固定幅を設定
          style={{ 
            display: 'block', /* 中央揃えのためにブロック要素にする */
            margin: '0 auto', /* 中央揃え */
            padding: '12px 25px', /* パディングで幅を調整 */
            marginTop: '10px', 
            borderRadius: '25px', /* 丸いボタン */
            border: 'none', 
            backgroundColor: '#007bff', 
            color: 'white', 
            cursor: 'pointer',
            fontSize: '1.1em',
            fontWeight: 'bold',
            transition: 'background-color 0.2s ease'
          }}
        >
          このコーデで確定
        </button>
      </div>

      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <Link to="/home" 
          style={{ 
            color: '#6c757d', 
            textDecoration: 'none', 
            fontSize: '0.9em',
            transition: 'color 0.2s ease'
          }}
        >
          相談をやめてホームページに戻る
        </Link>
      </div>
    </div>
  );
};

export default SuggestionPage;