"""
ベクトル類似度ユーティリティ

提供:
- cosine_similarity(a, b): 2ベクトルのcos類似度（ゼロベクトルは0.0）
- mean_cosine_similarity(vec, vecs): 1対多のcos類似度平均（空リストは0.0）
"""

from typing import Sequence

import numpy as np


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """2ベクトルのcos類似度を返す。ゼロベクトルは0.0として扱う。"""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def mean_cosine_similarity(vec: np.ndarray, vecs: Sequence[np.ndarray]) -> float:
    """
    vec と vecs の各ベクトルとのcos類似度の平均を返す。
    vecs が空の場合は 0.0。
    """
    if not vecs:
        return 0.0
    sims = [cosine_similarity(vec, v) for v in vecs]
    return float(np.mean(sims))
