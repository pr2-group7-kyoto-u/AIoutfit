const api = {
  register: (username: string, password: string) =>
    fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    }).then(res => res.json()),

  login: (username: string, password: string) =>
    fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    }).then(res => res.json()),

  addCloth: (userId: number, clothData: any) =>
    fetch('/api/clothes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, ...clothData }),
    }).then(res => res.json()),

  getClothes: (userId: number) =>
    fetch(`/api/clothes/${userId}`).then(res => res.json()),

  suggestOutfits: (userId: number, date: string, occasion: string, location: string) =>
    fetch('/api/suggest_outfits', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, date, occasion, location }),
    }).then(res => res.json()),

  updateUserPreferences: (userId: number, preferences: any) =>
    fetch(`/api/user_preferences/${userId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(preferences),
    }).then(res => res.json()),
};

export default api;