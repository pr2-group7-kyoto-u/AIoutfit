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
  preferred: boolean;
  available: boolean;
  image_url?: string; // 画像URLはオプショナル
}

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
      const fetchUserClothes = async () => {
        try {
          const result = await api.getClothes(user.id);
          if (Array.isArray(result)) setClothes(result);
        } catch (error) {
          console.error("Failed to fetch clothes:", error);
          setMessage("服の読み込みに失敗しました。");
        }
      };
      fetchUserClothes();
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
      // バックエンドのレスポンスにclothオブジェクトが含まれているか確認
      if (result.cloth) {
        // 成功したらフォームをリセット
        setNewClothName('');
        setNewClothCategory('');
        setNewClothColor('');
        setSelectedImageFile(null);
        // 服リストを再取得して画面を更新
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
        setOutfitSuggestions(result.suggestions);
      }
      setMessage(result.message || "コーデを提案しました。");
    } catch (error) {
      console.error("Failed to suggest outfits:", error);
      setMessage("コーデの提案に失敗しました。");
    }
  };

  const handleSetPreferred = async (clothID: number, preferred: boolean) => {
    if (!user) return;
    try {
      const result = await api.updateClothes(user.id, clothID, {Preferred: preferred});
      if (result) {
        setClothes(prevClothes =>
          prevClothes.map(cloth =>
            cloth.id === clothID ? { ...cloth, preferred: preferred } : cloth
          )
        );
      }
    } catch (error) {
      console.error("Failed to set to preferred:", error);
      setMessage("お気に入りに設定失敗しました。");
    }
  }

  const handleSetAvailabile = async (clothId: number, available: boolean) => {
    if (!user) return;
    try {
      const result = await api.updateClothes(user.id, clothId, {Available: available});
      if (result) {
        setClothes(prevClothes =>
          prevClothes.map(cloth =>
            cloth.id === clothId ? { ...cloth, available: available } : cloth
          )
        );
      }
    } catch (error) {
      console.error("Failed to set to available:", error);
      setMessage("利用可能に失敗しました。");
    }
  };

  const handleDeleteCloth = async (clothID: number) => {
    if (!user) return;
    try {
      const result = await api.deleteClothes(user.id, clothID);
      if (result) {
        setClothes(prevClothes =>
          prevClothes.filter(cloth => cloth.id !== clothID)
        );
      }
    } catch (error) {
      console.error("Failed to delete clothes:", error);
      setMessage("服の削除に失敗しました。");
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
        <input type="text" placeholder="カテゴリ (例: トップス)" value={newClothCategory} onChange={(e) => setNewClothCategory(e.target.value)} required />
        <input type="text" placeholder="色 (例: 黒)" value={newClothColor} onChange={(e) => setNewClothColor(e.target.value)} />
        
        <div>
          <label>画像 (任意): </label>
          <input type="file" accept="image/*" onChange={(e) => setSelectedImageFile(e.target.files ? e.target.files[0] : null)} />
        </div>

        <button type="submit">この服を登録する</button>
      </form>

      <h3>あなたの服</h3>
      {clothes.length === 0 ? (
        <p>まだ服が登録されていません。</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>名前</th>
              <th>色</th>
              <th>カテゴリ</th>
              <th>イメージ</th>
              <th>お気に入り</th>
              <th>利用可能</th>
              <th>削除</th>
            </tr>
          </thead>
          <tbody>
            {clothes.map((cloth) => (
              <tr key={cloth.id}>
                <td>{cloth.name}</td>
                <td>{cloth.color}</td>
                <td>{cloth.category}</td>
                <td><img src={cloth.image_url} alt={cloth.name} style={{height: '50px'}} /></td>
                <td><button onClick={() => handleSetPreferred(cloth.id, !cloth.preferred)}>{cloth.preferred ? "✔️" : "✖️"}</button></td>
                <td><button onClick={() => handleSetAvailabile(cloth.id, !cloth.available)}>{cloth.available ? "✔️" : "✖️"}</button></td>
                <td><button onClick={() => handleDeleteCloth(cloth.id)}>削除</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* コーデ提案フォームと結果表示は変更なし
      <ul>
        {clothes.map((cloth) => (
          <li key={cloth.id}>
            {cloth.name} ({cloth.color}, {cloth.category})
            {cloth.image_url && <img src={cloth.image_url} alt={cloth.name} style={{height: '50px', marginLeft: '10px'}} />}
          </li>
        ))}
      </ul> */}
      
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
