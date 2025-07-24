import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../hooks/useAuth';

// Cloth（服）の型を定義
interface Cloth {
  id: number;
  name: string;
  color: string;
  category: string;
  image_url?: string; // 画像URLはオプショナル（例: 153b4d1d-cff7-4035-a356-18e59d71c125.jpg）
}

// ★★★ MinIOのベースURLをコンポーネント内で定義 ★★★
const MINIO_BASE_URL = 'http://localhost:9000/images/';

const DashboardPage: React.FC = () => {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const navigate = useNavigate();

  // stateの定義
  const [clothes, setClothes] = useState<Cloth[]>([]);
  const [message, setMessage] = useState('');

  // 服登録フォーム用のstate
  const [newClothName, setNewClothName] = useState('');
  const [newClothCategory, setNewClothCategory] = useState('');
  const [newClothColor, setNewClothColor] = useState('');
  const [selectedImageFile, setSelectedImageFile] = useState<File | null>(null);

  // コーデ提案フォーム用のstate
  const [suggestedDate, setSuggestedDate] = useState('');
  const [occasion, setOccasion] = useState('');
  const [location, setLocation] = useState('Kyoto, Japan');
  const [outfitSuggestions, setOutfitSuggestions] = useState<any[]>([]);

  // 認証状態の確認とデータ取得
  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    if (user) {
      const fetchInitialData = async () => {
        try {
          const clothesResult = await api.getClothes(user.id);
          if (Array.isArray(clothesResult)) setClothes(clothesResult);

          const pastResult = await api.getPastSuggestions();
          if (Array.isArray(pastResult)) setOutfitSuggestions(pastResult);

        } catch (error) {
          console.error("Failed to fetch initial data:", error);
          setMessage("データの読み込みに失敗しました。");
        }
      };
      fetchInitialData();
    }
  }, [isLoading, isAuthenticated, user, navigate]);

  // 服の追加処理
  const handleAddCloth = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    if (!newClothName || !newClothCategory) {
      setMessage("服の名前とカテゴリは必須です。");
      return;
    }

    try {
      const clothData = {
        name: newClothName,
        category: newClothCategory,
        color: newClothColor,
      };
      
      const result = await api.addCloth(clothData, selectedImageFile);

      setMessage(result.message);
      if (result.cloth) {
        setNewClothName('');
        setNewClothCategory('');
        setNewClothColor('');
        setSelectedImageFile(null);
        const updatedClothes = await api.getClothes(user.id);
        if (Array.isArray(updatedClothes)) setClothes(updatedClothes);
      }
    } catch (error: any) {
      console.error("Failed to add cloth:", error);
      setMessage(error.message || "服の追加に失敗しました。");
    }
  };

  // コーデ提案処理
  const handleSuggestOutfits = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    try {
      const result = await api.suggestOutfits(user.id, suggestedDate, occasion, location);
      if (result.suggestions) {
        setOutfitSuggestions(prevSuggestions => [...result.suggestions, ...prevSuggestions]);
      }
      setMessage(result.message || "コーデを提案しました。");
    } catch (error: any) {
      console.error("Failed to suggest outfits:", error);
      setMessage("コーデの提案に失敗しました。");
    }
  };

  if (isLoading) {
    return <div>認証状態を読み込み中...</div>;
  }

  return (
    <div>
      <h2>ダッシュボード (ようこそ {user?.username} さん!)</h2>
      <div style={{ marginBottom: '20px' }}>
        <p>ユーザー情報: {user?.age && `${user.age}歳`} {user?.gender && `・ ${user.gender}`}</p>
      </div>
      <button onClick={logout} style={{ float: 'right' }}>ログアウト</button>
      <br/>
      <Link to="/suggest">AIとコーデを相談する</Link> 
      <br/>
      <Link to="/">ホームに戻る</Link>

      <h3>服の登録</h3>
      <form onSubmit={handleAddCloth}>
        <input type="text" placeholder="服の名前 (例: 半袖Tシャツ)" value={newClothName} onChange={(e) => setNewClothName(e.target.value)} required />
        <select value={newClothCategory} onChange={(e) => setNewClothCategory(e.target.value)} required>
          <option value="" disabled>カテゴリを選択</option>
          <option value="tops">トップス</option>
          <option value="bottoms">ボトムス</option>
          <option value="shoes">シューズ</option>
        </select>
        <select value={newClothColor} onChange={(e) => setNewClothColor(e.target.value)}>
          <option value="" disabled>色を選択 (任意)</option>
          <option value="黒">黒</option>
          <option value="白">白</option>
          <option value="グレー">グレー</option>
          <option value="ネイビー">ネイビー</option>
          <option value="ベージュ">ベージュ</option>
          <option value="ブラウン">ブラウン</option>
          <option value="グリーン">グリーン</option>
          <option value="青">青</option>
          <option value="赤">赤</option>
          <option value="その他">その他</option>
        </select>
        <div>
          <label>画像 (任意): </label>
          <input type="file" accept="image/*" onChange={(e) => setSelectedImageFile(e.target.files ? e.target.files[0] : null)} />
        </div>
        <button type="submit">この服を登録する</button>
      </form>

      <h3>あなたの服</h3>
      <ul>
        {clothes.map((cloth) => (
          <li key={cloth.id}>
            {cloth.name} ({cloth.color}, {cloth.category})
            {/* ▼▼▼ ここを修正 ▼▼▼ */}
            {cloth.image_url && (
              <>
                {console.log(`${MINIO_BASE_URL}${cloth.image_url}`)}
                <img 
                  src={`${MINIO_BASE_URL}${cloth.image_url}`} 
                  alt={cloth.name} 
                  style={{height: '50px', marginLeft: '10px'}} 
                />
              </>
            )}
            {/* ▲▲▲ ここまで修正 ▲▲▲ */}
          </li>
        ))}
      </ul>
      
      <h3>コーデ提案</h3>
      <form onSubmit={handleSuggestOutfits}>
        <label>日付: <input type="date" value={suggestedDate} onChange={(e) => setSuggestedDate(e.target.value)} required /></label><br />
        <label>外出先/シーン: <input type="text" placeholder="例: 仕事, デート" value={occasion} onChange={(e) => setOccasion(e.target.value)} required /></label><br />
        <label>場所: <input type="text" value={location} onChange={(e) => setLocation(e.target.value)} /></label><br />
        <button type="submit">コーデを提案する</button>
      </form>
      {message && <p>{message}</p>}
      
      <h3>提案されたコーデ</h3>
      {outfitSuggestions.length > 0 ? (
        <div>
          {outfitSuggestions.map((suggestion: any, index: number) => (
            <div key={suggestion.suggestion_id || index} style={{ border: '1px solid #ccc', margin: '10px', padding: '10px' }}>
              <h4>{suggestion.suggested_date ? `${suggestion.suggested_date}の提案` : `新しいコーデ ${index + 1}`}</h4>
              {suggestion.occasion_info && <p>シーン: {suggestion.occasion_info} ({suggestion.weather_info})</p>}
              <p>トップス: {suggestion.top?.name} ({suggestion.top?.color})</p>
              <p>ボトムス: {suggestion.bottom?.name} ({suggestion.bottom?.color})</p>
              {suggestion.outer && <p>アウター: {suggestion.outer?.name} ({suggestion.outer?.color})</p>}
              {suggestion.shoes && <p>シューズ: {suggestion.shoes?.name} ({suggestion.shoes?.color})</p>}
              {suggestion.reason && <p>理由: {suggestion.reason}</p>}
            </div>
          ))}
        </div>
      ) : (
        <p>過去の提案履歴はありません。フォームから新しいコーデを提案できます。</p>
      )}
    </div>
  );
};

export default DashboardPage;