// 認証付きのfetchリクエストを生成するヘルパー関数
const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
  const headers = new Headers(options.headers);

  // bodyがFormDataのインスタンスでない場合のみ、Content-Typeをセットする
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const token = localStorage.getItem('access_token');

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(url, { ...options, headers });

  if (response.status === 401 || response.status === 422) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('username');
    window.location.href = '/login';
    return Promise.reject(new Error('Session expired'));
  }

  return response;
};

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface DialogueSlots {
  [key: string]: string | null;
}
export interface HistoryMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface SuggestionItems {
  tops: string;
  bottoms: string;
  shoes: string;
  outerwear?: string | null;
}

const api = {
  register: (username: string, password: string, age?: string, gender?: string) =>
    fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, age, gender }),
    }).then(res => res.json()),

  login: (username: string, password: string) =>
    fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    }).then(res => res.json()),

  getClothes: async (userId: number) => {
    const response = await fetchWithAuth(`/api/clothes/${userId}`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'サーバーエラー' }));
      throw new Error(errorData.message);
    }
    return response.json();
  },

  addCloth: async (clothData: { [key: string]: any }, imageFile: File | null) => {
    const formData = new FormData();
    Object.keys(clothData).forEach(key => {
      if (clothData[key] != null) {
        formData.append(key, String(clothData[key]));
      }
    });
    if (imageFile) {
      formData.append('image', imageFile);
    }
    const response = await fetchWithAuth('/api/clothes', {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'サーバーエラー' }));
      throw new Error(errorData.message);
    }
    return response.json();
  },

  getPastSuggestions: async () => {
    const response = await fetchWithAuth('/api/suggestions');
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'サーバーエラー' }));
      throw new Error(errorData.message);
    }
    return response.json();
  },

  saveSuggestion: async (suggestionData: {
    suggested_date: string;
    top_id: number;
    bottom_id: number;
    shoes_id?: number;
  }) => {
    const response = await fetchWithAuth('/api/suggestions', {
      method: 'POST',
      body: JSON.stringify(suggestionData),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'サーバーエラー' }));
      throw new Error(errorData.message);
    }
    return response.json();
  },

  suggestOutfits: async (userId: number, date: string, occasion: string, location: string) => {
    const response = await fetchWithAuth('/api/suggest_outfits', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, date, occasion, location }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'サーバーエラー' }));
      throw new Error(errorData.message);
    }
    return response.json();
  },

  updateUserPreferences: async (userId: number, preferences: any) => {
    const response = await fetchWithAuth(`/api/user_preferences/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(preferences),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'サーバーエラー' }));
      throw new Error(errorData.message);
    }
    return response.json();
  },

  chatWithAI: async (messages: Message[]) => {
    const response = await fetchWithAuth('/api/chat', {
      method: 'POST',
      // 'message' ではなく 'messages' というキーで会話履歴全体を送信
      body: JSON.stringify({ messages }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'サーバーエラー' }));
      throw new Error(errorData.message);
    }
    return response.json();
  },

  proposeOutfit: async (slots: DialogueSlots, history: HistoryMessage[], message: string) => {
    const response = await fetchWithAuth('/api/propose', {
      method: 'POST',
      body: JSON.stringify({ slots, history, message }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'サーバーエラー' }));
      throw new Error(errorData.message);
    }
    return response.json();
  },

  fetchOutfitImages: async (payload: SuggestionItems) => {
    const response = await fetchWithAuth('/api/search/outfit', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ message: 'サーバーエラー' }));
      throw new Error(err.message);
    }
    console.log("fetchOutfitImages response:", response);
    return response.json();   // ← ResultPage で受け取る { tops: [..], bottoms: [..], shoes: [..] }
    // return response.blob(); // ← ResultPage で受け取る { tops: Blob, bottoms: Blob, shoes: Blob }
  },
  updateClothes: async (userId: number, clothesId: number, clothes_info: any) => {
    const response = await fetchWithAuth(`/api/clothes/${userId}/${clothesId}`, {
      method: 'PATCH',
      body: JSON.stringify(clothes_info),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'サーバーエラー' }));
      throw new Error(errorData.message);
    }
    return response.json();
  },

  deleteClothes: async (userId: number, clothesId: number) => {
    const response = await fetchWithAuth(`/api/clothes/${userId}/${clothesId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'サーバーエラー' }));
      throw new Error(errorData.message);
    }
    return response.json();
  },
};

export default api;
export const { fetchOutfitImages } = api;