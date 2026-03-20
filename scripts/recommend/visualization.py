"""
recommend 用 map.html 再生成（top_clusters ハイライト付き）

提供:
- regenerate_map_html(map_data, top_clusters, ser_top, html_path): 色分けして map.html を更新
"""

from pathlib import Path
from typing import Any

import numpy as np


def regenerate_map_html(
    map_data: dict[str, Any],
    top_clusters: list[dict[str, Any]],
    ser_top: list[dict[str, Any]],
    html_path: Path,
) -> None:
    """
    datamapplot で map.html を再生成する。
    top_clusters はオレンジ、セレンディピティ隣接クラスタは緑、それ以外は青。
    map_data に papers が含まれない場合はスキップ。
    """
    if not map_data.get("papers"):
        print("[INFO] Skipping map.html regeneration (papers data not found in map.json)")
        return

    import datamapplot

    top_labels = {c["label"] for c in top_clusters}
    ser_labels = {c["label"] for c in ser_top}
    papers = map_data["papers"]
    cluster_label_map = {c["id"]: c["label"] for c in map_data["clusters"]}

    coords = np.array([[p["umap_x"], p["umap_y"]] for p in papers])
    point_labels = np.array(
        [cluster_label_map.get(p["cluster_id"], "Unlabelled") for p in papers]
    )
    all_labels = {c["label"] for c in map_data["clusters"]}
    label_color_map = {
        label: (
            "#f59e0b" if label in top_labels
            else "#10b981" if label in ser_labels
            else "#3b82f6"
        )
        for label in all_labels
    }

    plot = datamapplot.create_interactive_plot(
        coords,
        point_labels,
        hover_text=np.array([p["id"] for p in papers]),
        title="arXiv Paper Map",
        enable_search=True,
        noise_label="Unlabelled",
        label_color_map=label_color_map,
        inline_data=True,
    )
    html_path.parent.mkdir(parents=True, exist_ok=True)
    plot.save(str(html_path))
    print("[INFO] Updated map.html with top_clusters highlighted")
