// src/pages/ResultPage.tsx
import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { fetchOutfitImages } from "../api"; // ← 追加: /api/search/outfit を呼び出すヘルパ
import { useAuth } from "../hooks/useAuth";

/** 確定したコーデ (SuggestionPage → navigate state で受け取る) */
interface SuggestionItems {
  tops: string;
  bottoms: string;
  shoes: string;
  outerwear?: string | null; // outer が無い場合もある
}

/** Pinecone → API → フロントに返ってくる 1 件の検索結果 */
interface Match {
  image_url: string;
  score: number;
  metadata: {
    description?: string;
    category?: string;
  };
}

/** /api/search/outfit のレスポンス型 */
type SearchResponse = {
  tops?: Match[];
  bottoms?: Match[];
  outerwear?: Match[];
  shoes?: Match[];
};

const ResultPage: React.FC = () => {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [images, setImages] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  /** SuggestionPage から受け取った確定コーデ。直接アクセスの場合は undefined */
  const suggestion = state?.suggestion as SuggestionItems | undefined;

  /**
   * コンポーネント初期化時:
   *  1. suggestion が無ければダッシュボードへリダイレクト
   *  2. suggestion をクエリとして /api/search/outfit を呼び、画像 URL を取得
   */
  useEffect(() => {
    if (!suggestion) {
      // リロード直後など state が無い場合のフォールバック
      navigate("/dashboard");
      return;
    }

    const run = async () => {
      try {
        const { data } = await fetchOutfitImages(suggestion);
        console
        setImages(data);
      } catch (err) {
        console.error("画像検索に失敗しました", err);
      } finally {
        setIsLoading(false);
      }
    };
    run();
  }, [suggestion, navigate]);

  /** カテゴリの表示順を決める */
  const categories: (keyof SuggestionItems)[] = [
    "tops",
    "bottoms",
    "outerwear",
    "shoes",
  ];

  /**
   * MinIO など相対パスの場合にドメインを補完するユーティリティ
   * env 例: REACT_APP_MINIO_PUBLIC_URL="https://cdn.myapp.com"
   */
  const toFullUrl = (path?: string) => {
    if (!path) return "";
    if (path.startsWith("http")) return path;
    return `${process.env.REACT_APP_MINIO_PUBLIC_URL || ""}${path}`;
  };

  if (!suggestion) return null; // 取得中は何も表示しない

  return (
    <div style={{ padding: 20 }}>
      <h2>確定したコーディネート</h2>

      {/* --- テキストでコーデ内容を表示 --- */}
      <ul>
        {categories.map((c) =>
          suggestion[c] ? (
            <li key={c}>
              <strong>
                {c.charAt(0).toUpperCase() + c.slice(1)}:
              </strong>{" "}
              {suggestion[c as keyof SuggestionItems]}
            </li>
          ) : null
        )}
      </ul>

      <hr style={{ margin: "24px 0" }} />

      {/* --- 画像表示エリア --- */}
      {isLoading && <p>画像を検索中...</p>}

      {!isLoading && images && (
        <div
          style={{
            display: "grid",
            gap: 20,
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          }}
        >
          {categories.map((c) => {
            const matches = images[c as keyof SearchResponse];
            if (!matches || matches.length === 0) return null;
            const best = matches[0]; // top-1 を表示 (複数表示したい場合は map)
            return (
              <div key={c}>
                <img
                  src={toFullUrl(best.image_url)}
                  alt={best.metadata?.description || c}
                  style={{
                    width: "100%",
                    aspectRatio: "3/4",
                    objectFit: "cover",
                    borderRadius: 8,
                  }}
                />
                {best.metadata?.description && (
                  <p style={{ marginTop: 8, fontSize: 14 }}>
                    {best.metadata.description}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}

      <button
        onClick={() => navigate("/dashboard")}
        style={{ marginTop: 32, padding: "10px 20px" }}
      >
        ダッシュボードに戻る
      </button>
    </div>
  );
};

export default ResultPage;
