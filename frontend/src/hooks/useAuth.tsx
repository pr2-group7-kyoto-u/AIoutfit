import { useState, useEffect, useCallback, createContext, useContext, ReactNode } from 'react';
import api from '../api';

// ユーザー情報の型定義
interface User {
  id: number;
  username: string;
}

// 認証コンテキストの型定義
interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<{ success: boolean; message: string }>;
  logout: () => void;
  isAuthenticated: boolean;
}

// 認証コンテキストを作成
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// AuthProvider コンポーネント
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true); // 認証状態の読み込み中フラグ
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // コンポーネントマウント時に認証状態を初期化
  useEffect(() => {
    const initializeAuth = () => {
      const storedUserId = localStorage.getItem('user_id');
      const storedUsername = localStorage.getItem('username');
      if (storedUserId && storedUsername) {
        setUser({ id: parseInt(storedUserId), username: storedUsername });
        setIsAuthenticated(true);
      }
      setIsLoading(false);
    };
    initializeAuth();
  }, []);

  // ログイン処理
  const login = useCallback(async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const result = await api.login(username, password);
      if (result.user_id) {
        const newUser: User = { id: result.user_id, username: username };
        setUser(newUser);
        setIsAuthenticated(true);
        localStorage.setItem('user_id', result.user_id.toString());
        localStorage.setItem('username', username);
        return { success: true, message: result.message };
      } else {
        setUser(null);
        setIsAuthenticated(false);
        return { success: false, message: result.message || 'ログインに失敗しました。' };
      }
    } catch (error: any) {
      console.error("Login API call failed:", error);
      setUser(null);
      setIsAuthenticated(false);
      return { success: false, message: error.message || 'ネットワークエラーが発生しました。' };
    } finally {
      setIsLoading(false);
    }
  }, []);

  // ログアウト処理
  const logout = useCallback(() => {
    setUser(null);
    setIsAuthenticated(false);
    localStorage.clear(); // ローカルストレージの認証情報をクリア
  }, []);

  const authContextValue = {
    user,
    isLoading,
    login,
    logout,
    isAuthenticated,
  };

  return (
     <AuthContext.Provider value={authContextValue}>
       {children}
      </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};