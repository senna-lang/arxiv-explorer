/**
 * arXiv新聞アプリの共通型定義
 *
 * Paper: data/YYYYMMDD.json の各論文エントリ
 * Rating: data/ratings.json の各評価エントリ
 * DailyData: data/YYYYMMDD.json のルート構造
 */

export type Paper = {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  url: string;
  categories: string[];
  submitted: string;
  score: number;
  github_url?: string;
};

export type Rating = {
  paper_id: string;
  title: string;
  abstract: string;
  rating: 1 | 2 | 3;
  rated_at: string;
};

export type DailyData = {
  date: string;
  collected_at: string;
  papers: Paper[];
  meta: {
    total: number;
    model: string;
    profile_version: string;
  };
};

export type RatingsData = {
  ratings: Rating[];
};

export type Cluster = {
  id: number;
  keywords: string[];
  label: string;
  centroid: number[];
  paper_ids: string[];
  size: number;
  umap_x: number;
  umap_y: number;
};

/** map.json 内の個別論文エントリ（座標 + クラスタID） */
export type MapPaper = {
  id: string;
  title?: string;
  abstract?: string;
  umap_x: number;
  umap_y: number;
  cluster_id: number | null;
};

export type MapData = {
  generated_at: string;
  total_papers: number;
  model: string;
  clusters: Cluster[];
  papers: MapPaper[];
};

/** ダッシュボードで表示する論文の統合型（map座標 + 日次データの詳細） */
export type DashboardPaper = MapPaper & {
  /** 日次JSONからマージされた詳細情報（存在する場合のみ） */
  abstract?: string;
  authors?: string[];
  url: string;
  categories?: string[];
  submitted?: string;
  score?: number;
  github_url?: string;
};

/** ダッシュボードのフィルタ状態 */
export type FilterState = {
  keyword: string;
  scoreRange: [number, number];
  selectedClusterIds: Set<number>;
};

export type Recommendation = {
  id: string;
  title: string;
  abstract: string;
  url: string;
  match_score: number;
  matched_cluster: string;
  submitted: string;
};

export type TopCluster = {
  label: string;
  score: number;
};

/** Recommendation と同じ構造だが意味的に区別するためのエイリアス */
export type SerendipityPaper = Recommendation;

export type RecommendationsData = {
  generated_at: string;
  top_clusters: TopCluster[];
  recommendations: Recommendation[];
  serendipity_clusters?: TopCluster[];
  serendipity?: SerendipityPaper[];
};
