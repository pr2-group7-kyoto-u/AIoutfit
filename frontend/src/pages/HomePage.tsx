// src/pages/HomePage.tsx
import React, { useState, useEffect } from 'react'; // ★useState, useEffect を追加
import { Link, useNavigate } from 'react-router-dom'; // navigate を追加
import styles from './normal.module.css';
import { useAuth } from '../hooks/useAuth'; // ★useAuth をインポート

const HomePage: React.FC = () => {
  const { user, isAuthenticated, isLoading } = useAuth(); // ★user, isAuthenticated, isLoading を取得
  const navigate = useNavigate(); // ★navigate を取得（今回は直接使わないが、認証フックとセットでインポート）

  // 認証状態の確認 (HomePageでは通常ログインページへの強制リダイレクトはしませんが、
  // ユーザー情報の読み込み完了を待つために isLoading を使います)
  useEffect(() => {
    // 認証状態の読み込みが完了するのを待つ
    if (isLoading) return; 

    // もしログイン済みでない場合に特定のメッセージを表示したい場合など、
    // ここで isAuthenticated を利用できます。
    // 例:
    // if (!isAuthenticated) {
    //   // ログインしていない場合の特別な処理やメッセージ表示
    // }
  }, [isLoading, isAuthenticated]);


  // 読み込み中の表示
  // userオブジェクトへのアクセス前に isLoading をチェックすることが重要
  if (isLoading) {
    return (
      <div className={styles.normalBackground}>
        <div className={styles.mainContentArea}>
          <h1>Loading...</h1> {/* ローディング中に表示する内容 */}
          <p>ユーザー情報を読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.normalBackground}>
      <div className={styles.mainContentArea}> 
        <h1>AIoutfit</h1>
        {/* ★ここから修正: user オブジェクトの存在をチェックして表示を切り替える ★ */}
        {user ? ( // user オブジェクトが存在する場合（＝ログインしている場合）
          <p>ようこそ {user.username} さん！</p>
        ) : (
          // user がいない場合（＝ログインしていない、または読み込み中だがuserがnullだった場合）
          <p>あなたのコーディネートをサポートします！</p>
        )}
        {/* ★ここまで修正 ★ */}
        
        <ul>
          <li><Link to="/uploadclothing">服を登録</Link></li>
          <li><Link to="/checkclothing">服を確認</Link></li>
          <li><Link to="/suggest">服の提案を受ける</Link></li>
          <li><Link to="/history">履歴</Link></li>
        </ul>
      </div>
    </div>
  );
};

export default HomePage;