import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../hooks/useAuth';

const DashboardPage: React.FC = () => {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const navigate = useNavigate();

  // 未認証ならログインページにリダイレクト
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/login');
    }
  }, [isLoading, isAuthenticated, navigate]);

  const userId = user ? user.id : 0;
  const [clothes, setClothes] = useState([]);
  const [newClothName, setNewClothName] = useState('');
  const [newClothCategory, setNewClothCategory] = useState('');
  const [newClothColor, setNewClothColor] = useState('');

  const [suggestedDate, setSuggestedDate] = useState('');
  const [occasion, setOccasion] = useState('');
  const [location, setLocation] = useState('Kyoto, Japan');
  const [outfitSuggestions, setOutfitSuggestions] = useState([]);
  const [message, setMessage] = useState('');

  const fetchClothes = useCallback(async () => {
    if (!userId || isNaN(userId)) {
      return;
    }
    try {
      const result = await api.getClothes(userId);
      setClothes(result);
    } catch (error) {
      console.error("Failed to fetch clothes:", error);
      setMessage("服の読み込みに失敗しました。");
    }
  }, [userId]);

  useEffect(() => {
    fetchClothes();
  }, [fetchClothes]);

  const handleAddCloth = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      setMessage("ログインしていません。");
      return;
    }

    if (!newClothName || !newClothCategory || !newClothColor) {
        setMessage("服の名前、カテゴリ、色は必須です。");
        return;
    }

    try {
      const result = await api.addCloth(user.id, {
        name: newClothName,
        category: newClothCategory,
        color: newClothColor,
      });
      setMessage(result.message);
      if (result.cloth_id) {
        setNewClothName('');
        setNewClothCategory('');
        setNewClothColor('');
        fetchClothes();
      }
    } catch (error) {
      console.error("Failed to add cloth:", error);
      setMessage("服の追加に失敗しました。");
    }
  };

  const handleSuggestOutfits = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!suggestedDate || !occasion) {
      setMessage("日付と外出先は必須です。");
      return;
    }
    if (!user) {
        setMessage("ログインしていません。");
        return;
    }

    try {
      const result = await api.suggestOutfits(user.id, suggestedDate, occasion, location);
      if (result.suggestions) {
        setOutfitSuggestions(result.suggestions);
      }
      setMessage(result.message || "コーデを提案しました。");
    } catch (error) {
      console.error("Failed to suggest outfits:", error);
      setMessage("コーデの提案に失敗しました。");
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (isLoading) {
    return <div>認証状態を読み込み中...</div>; // 読み込み中の表示
  }

  return (
    <div>
      <h2>ダッシュボード (ようこそ {user?.username} さん!)</h2> {/* ユーザー名を表示 */}
      <button onClick={handleLogout} style={{ float: 'right' }}>ログアウト</button>
      <Link to="/">ホームに戻る</Link>

      <h3>服の登録</h3>
      <form onSubmit={handleAddCloth}>
        <input type="text" placeholder="服の名前 (例: 半袖Tシャツ)" value={newClothName} onChange={(e) => setNewClothName(e.target.value)} />
        <input type="text" placeholder="カテゴリ (例: トップス)" value={newClothCategory} onChange={(e) => setNewClothCategory(e.target.value)} />
        <input type="text" placeholder="色 (例: 黒)" value={newClothColor} onChange={(e) => setNewClothColor(e.target.value)} />
        <button type="submit">服を追加</button>
      </form>

      <h3>あなたの服</h3>
      {clothes.length === 0 ? (
        <p>まだ服が登録されていません。</p>
      ) : (
        <ul>
          {clothes.map((cloth: any) => (
            <li key={cloth.id}>{cloth.name} ({cloth.color}, {cloth.category})</li>
          ))}
        </ul>
      )}

      <h3>コーデ提案</h3>
      <form onSubmit={handleSuggestOutfits}>
        <label>
          日付: <input type="date" value={suggestedDate} onChange={(e) => setSuggestedDate(e.target.value)} required />
        </label><br />
        <label>
          外出先/シーン: <input type="text" placeholder="例: 仕事, デート, 普段使い" value={occasion} onChange={(e) => setOccasion(e.target.value)} required />
        </label><br />
        <label>
          場所: <input type="text" placeholder="例: Kyoto, Japan" value={location} onChange={(e) => setLocation(e.target.value)} />
        </label><br />
        <button type="submit">コーデを提案する</button>
      </form>
      {message && <p>{message}</p>}

      <h3>提案されたコーデ</h3>
      {outfitSuggestions.length === 0 ? (
        <p>まだ提案されたコーデはありません。</p>
      ) : (
        <div>
          {outfitSuggestions.map((suggestion: any, index: number) => (
            <div key={index} style={{ border: '1px solid #ccc', margin: '10px', padding: '10px' }}>
              <h4>コーデ {index + 1}</h4>
              <p>トップス: {suggestion.top?.name} ({suggestion.top?.color})</p>
              <p>ボトムス: {suggestion.bottom?.name} ({suggestion.bottom?.color})</p>
              {suggestion.outer && <p>アウター: {suggestion.outer?.name} ({suggestion.outer?.color})</p>}
              <p>理由: {suggestion.reason}</p>
              {suggestion.recommended_product && (
                <div>
                  <h5>おすすめ商品:</h5>
                  <p>{suggestion.recommended_product.name}</p>
                  {suggestion.recommended_product.image_url && <img src={suggestion.recommended_product.image_url} alt={suggestion.recommended_product.name} style={{ maxWidth: '100px' }} />}
                  {suggestion.recommended_product.buy_link && <p><a href={suggestion.recommended_product.buy_link} target="_blank" rel="noopener noreferrer">購入する</a></p>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* TODO: ユーザー設定 (パーソナルカラーなど) 画面を追加 */}
    </div>
  );
};

export default DashboardPage;