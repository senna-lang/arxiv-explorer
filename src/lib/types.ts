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
  rating: number;
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

export type MapData = {
  generated_at: string;
  total_papers: number;
  model: string;
  clusters: Cluster[];
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

export type RecommendationsData = {
  generated_at: string;
  top_clusters: TopCluster[];
  recommendations: Recommendation[];
};
