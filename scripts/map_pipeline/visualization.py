"""
datamapplot による論文地図 HTML 生成

提供:
- generate_map_html(umap_2d, paper_ids, topic_to_label, html_path): map.html を生成
"""

from pathlib import Path
from typing import Any

import numpy as np


def generate_map_html(
    umap_2d: np.ndarray,
    paper_ids: list[str],
    topic_to_label: dict[int, str],
    topics: list[int],
    html_path: Path,
    label_color_map: dict[str, str] | None = None,
) -> None:
    """
    datamapplot でインタラクティブな論文地図 HTML を生成して保存する。

    Args:
        umap_2d: UMAP 2D 座標 (N, 2)
        paper_ids: 各論文の arXiv ID リスト
        topic_to_label: topic_id → ラベル文字列のマッピング
        topics: 各論文の topic_id リスト（-1 はノイズ）
        html_path: 出力先 HTML パス
        label_color_map: ラベル → カラーコードのマッピング（省略時はデフォルト色）
    """
    import datamapplot

    point_labels = np.array(
        [topic_to_label.get(topics[i], "Unlabelled") for i in range(len(paper_ids))]
    )
    hover_texts = np.array(paper_ids)

    kwargs: dict[str, Any] = {
        "title": "arXiv Paper Map",
        "enable_search": True,
        "noise_label": "Unlabelled",
        "inline_data": True,
    }
    if label_color_map is not None:
        kwargs["label_color_map"] = label_color_map

    plot = datamapplot.create_interactive_plot(
        umap_2d,
        point_labels,
        hover_text=hover_texts,
        **kwargs,
    )
    html_path.parent.mkdir(parents=True, exist_ok=True)
    plot.save(str(html_path))
    print(f"[INFO] Saved map.html to {html_path}")
