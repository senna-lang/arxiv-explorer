"""
クラスタ集約ユーティリティ

提供:
- generate_label(keywords): キーワードリストからラベル文字列を生成
- build_cluster_dict(...): クラスタ情報を map.json スキーマの dict に変換
- build_map_output(...): map.json のルート構造を組み立てる
"""

from datetime import datetime
from typing import Any

from core.config import JST


def generate_label(keywords: list[str]) -> str:
    """
    クラスタキーワードから人間可読なラベルを生成する。
    先頭3キーワードを ' & ' で結合する。
    """
    if not keywords:
        return "unknown"
    return " & ".join(keywords[:3])


def build_cluster_dict(
    topic_id: int,
    keywords: list[str],
    centroid: list[float],
    paper_ids: list[str],
    umap_x: float,
    umap_y: float,
) -> dict[str, Any]:
    """クラスタ情報を map.json のスキーマに準拠した dict に変換する。"""
    return {
        "id": topic_id,
        "keywords": keywords,
        "label": generate_label(keywords),
        "centroid": centroid,
        "paper_ids": paper_ids,
        "size": len(paper_ids),
        "umap_x": round(umap_x, 4),
        "umap_y": round(umap_y, 4),
    }


def build_map_output(
    clusters: list[dict[str, Any]],
    papers: list[dict[str, Any]],
    total_papers: int,
    model: str,
) -> dict[str, Any]:
    """
    map.json のルート構造を組み立てる。
    papers は論文単位の UMAP 2D 座標と cluster_id を含む（datamapplot 用）。
    """
    return {
        "generated_at": datetime.now(JST).isoformat(),
        "total_papers": total_papers,
        "model": model,
        "clusters": clusters,
        "papers": papers,
    }
