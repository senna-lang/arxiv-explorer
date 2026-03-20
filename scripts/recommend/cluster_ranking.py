"""
クラスタランキング・スコアリング関数

提供:
- compute_instance_score(centroid, rated_vecs): centroid と高評価論文の cos 類似度平均
- compute_alpha(n_ratings, threshold): ratings 件数に応じた α 値
- compute_final_score(instance, profile, alpha): α 加重合成スコア
- rank_clusters(clusters, rated_vecs, profile_vecs, alpha): クラスタを final_score で降順ソート
- fetch_papers_for_cluster(paper_ids): arXiv API でクラスタ内論文情報を取得
"""

from typing import Any

import arxiv
import numpy as np

from core.similarity import mean_cosine_similarity


def compute_instance_score(centroid: np.ndarray, rated_vecs: list[np.ndarray]) -> float:
    """
    クラスタ centroid と高評価論文ベクトル群の cos 類似度平均を返す。
    rated_vecs が空の場合は 0.0。
    """
    return mean_cosine_similarity(centroid, rated_vecs)


def compute_alpha(n_ratings: int, threshold: int) -> float:
    """
    ratings 件数に応じた α 値を返す。
    0件=0.0、threshold件以上=1.0、線形補間。
    """
    return min(1.0, n_ratings / threshold)


def compute_final_score(instance: float, profile: float, alpha: float) -> float:
    """
    instance_score と profile_score を α 加重合成する。
    final = α * instance + (1-α) * profile
    """
    return alpha * instance + (1 - alpha) * profile


def rank_clusters(
    clusters: list[dict[str, Any]],
    rated_vecs: list[np.ndarray],
    profile_vecs: list[np.ndarray],
    alpha: float,
) -> list[dict[str, Any]]:
    """
    クラスタリストを final_score で降順ソートして返す。
    各クラスタに score フィールドを追加する。
    """
    scored = []
    for cluster in clusters:
        centroid = np.array(cluster["centroid"])
        instance = compute_instance_score(centroid, rated_vecs)
        profile = compute_instance_score(centroid, profile_vecs)
        score = compute_final_score(instance, profile, alpha)
        scored.append({**cluster, "score": round(score, 4)})
    return sorted(scored, key=lambda c: c["score"], reverse=True)


def fetch_papers_for_cluster(paper_ids: list[str]) -> list[Any]:
    """クラスタ内の arXiv ID で論文情報を取得する。"""
    if not paper_ids:
        return []
    client = arxiv.Client()
    search = arxiv.Search(id_list=paper_ids[:100])  # API 制限のため上限 100
    return list(client.results(search))
