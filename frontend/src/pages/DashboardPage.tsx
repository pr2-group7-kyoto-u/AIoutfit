import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api';
import { useAuth } from '../hooks/useAuth';
import ImageUpload from '../components/ImageUpload';

interface Cloth {
  id: number;
  name: string;
  color: string;
  category: string;
}

const DashboardPage: React.FC = () => {
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const navigate = useNavigate();

  const [clothes, setClothes] = useState<Cloth[]>([]);
  const [newClothName, setNewClothName] = useState('');
  const [newClothCategory, setNewClothCategory] = useState('');
  const [newClothColor, setNewClothColor] = useState('');
  const [suggestedDate, setSuggestedDate] = useState('');
  const [occasion, setOccasion] = useState('');
  const [location, setLocation] = useState('Kyoto, Japan');
  const [outfitSuggestions, setOutfitSuggestions] = useState<any[]>([]);
  const [message, setMessage] = useState('');
  const [uploadedImageUrl, setUploadedImageUrl] = useState('');

  useEffect(() => {
    // 認証状態の読み込みが完了するまで待つ
    if (isLoading) {
      return; 
    }
    // 認証されていない場合はログインページへ
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    // 認証済みでユーザー情報がある場合、服のデータを取得
    if (user) {
      const fetchUserClothes = async () => {
        try {
          const result = await api.getClothes(user.id);
          if (Array.isArray(result)) {
            setClothes(result);
          }
        } catch (error) {
          console.error("Failed to fetch clothes:", error);
          setMessage("服の読み込みに失敗しました。");
        }
      };
      fetchUserClothes();
    }
  }, [isLoading, isAuthenticated, user, navigate]); // 認証状態とuserの変更を監視

  
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
        // 服を追加したあと、リストを再取得（すでにあるuseEffectがuserの変更を検知しないため、手動で再取得）
        const updatedClothes = await api.getClothes(user.id);
        if (Array.isArray(updatedClothes)) setClothes(updatedClothes);
      }
    } catch (error) {
      console.error("Failed to add cloth:", error);
      setMessage("服の追加に失敗しました。");
    }
  };

  const handleSuggestOutfits = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
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
    // navigate('/login'); useAuth内のlogoutで処理されるか、useEffectで検知される
  };
  
  // 認証状態の読み込み中はスピナーなどを表示
  if (isLoading) {
    return <div>認証状態を読み込み中...</div>;
  }

  const handleUploadSuccess = (data: { image_url: string }) => {
    console.log('アップロード成功:', data);
    setUploadedImageUrl(data.image_url);
  };
  
  return (
    <div>
      <h2>ダッシュボード (ようこそ {user?.username} さん!)</h2>
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
          {clothes.map((cloth) => (
            <li key={cloth.id}>{cloth.name} ({cloth.color}, {cloth.category})</li>
          ))}
        </ul>
      )}

      <hr />
      <h3>画像のアップロードテスト</h3>
      <ImageUpload onUploadSuccess={handleUploadSuccess} />
      {uploadedImageUrl && (
        <div>
          <h4>アップロードされた画像:</h4>
          <img src={uploadedImageUrl} alt="アップロードされた画像" style={{ maxWidth: '200px' }} />
        </div>
      )}

      {/* コーデ提案フォームと結果表示は変更なし */}
      <h3>コーデ提案</h3>
      <form onSubmit={handleSuggestOutfits}>
        <label>日付: <input type="date" value={suggestedDate} onChange={(e) => setSuggestedDate(e.target.value)} required /></label><br />
        <label>外出先/シーン: <input type="text" placeholder="例: 仕事, デート" value={occasion} onChange={(e) => setOccasion(e.target.value)} required /></label><br />
        <label>場所: <input type="text" value={location} onChange={(e) => setLocation(e.target.value)} /></label><br />
        <button type="submit">コーデを提案する</button>
      </form>
      {message && <p>{message}</p>}
      
      <h3>提案されたコーデ</h3>
      {outfitSuggestions.length > 0 && (
        <div>
          {outfitSuggestions.map((suggestion: any, index: number) => (
            <div key={index} style={{ border: '1px solid #ccc', margin: '10px', padding: '10px' }}>
              <h4>コーデ {index + 1}</h4>
              <p>トップス: {suggestion.top?.name} ({suggestion.top?.color})</p>
              <p>ボトムス: {suggestion.bottom?.name} ({suggestion.bottom?.color})</p>
              {suggestion.outer && <p>アウター: {suggestion.outer?.name} ({suggestion.outer?.color})</p>}
              <p>理由: {suggestion.reason}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DashboardPage;