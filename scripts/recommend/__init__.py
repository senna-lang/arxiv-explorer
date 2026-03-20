"""
recommend パッケージ — おすすめ論文生成パイプライン

主なエントリポイント:
- main(top_clusters, top_n, log): ratings + map → recommendations の一連の処理
"""

from .cluster_ranking import (
    compute_alpha,
    compute_final_score,
    compute_instance_score,
    rank_clusters,
)
from .serendipity import select_serendipity_papers

__all__ = [
    "compute_instance_score",
    "compute_alpha",
    "compute_final_score",
    "rank_clusters",
    "select_serendipity_papers",
]
