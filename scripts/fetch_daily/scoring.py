"""
論文スコアリングモジュール

提供:
- score_papers(papers, vecs, rated_vecs, profile_vecs, alpha, top_n): α-blend スコアで上位N件を返す
"""

from typing import Any

import numpy as np

from core.similarity import mean_cosine_similarity


def score_papers(
    papers: list[dict[str, Any]],
    vecs: np.ndarray,
    rated_vecs: list[np.ndarray],
    profile_vecs: list[np.ndarray],
    alpha: float,
    top_n: int,
) -> list[dict[str, Any]]:
    """
    各論文の埋め込みベクトルと rated_vecs / profile_vecs の cos 類似度から
    α-blend スコアを計算し、スコア降順で top_n 件を返す。

    score = α × mean_cosine(vec, rated_vecs) + (1-α) × mean_cosine(vec, profile_vecs)
    """
    scored: list[dict[str, Any]] = []
    for paper, vec in zip(papers, vecs):
        instance_score = mean_cosine_similarity(vec, rated_vecs)
        profile_score = mean_cosine_similarity(vec, profile_vecs)
        final_score = alpha * instance_score + (1 - alpha) * profile_score
        scored.append({**paper, "score": round(final_score, 4)})

    scored.sort(key=lambda p: p["score"], reverse=True)
    return scored[:top_n]
