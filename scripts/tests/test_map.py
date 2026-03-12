"""
scripts/map.py のユニットテスト

テスト対象:
- build_cluster_dict: クラスタdictのスキーマ検証
- generate_label: keywordsからラベル文字列を生成
- build_map_output: map.json全体のスキーマ検証
"""

import sys
import os
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from map import build_cluster_dict, generate_label, build_map_output


SAMPLE_KEYWORDS = ["inference", "latency", "throughput", "serving", "quantization"]
SAMPLE_CENTROID = list(np.random.default_rng(0).random(768).tolist())
SAMPLE_PAPER_IDS = ["2503.12345", "2502.98765"]


class TestGenerateLabel:
    def test_joins_top_keywords(self):
        label = generate_label(["inference", "latency", "throughput"])
        assert "inference" in label
        assert "latency" in label

    def test_uses_at_most_three_keywords(self):
        label = generate_label(["a", "b", "c", "d", "e"])
        parts = label.split(" & ")
        assert len(parts) <= 3

    def test_empty_keywords_returns_unknown(self):
        label = generate_label([])
        assert label == "unknown"

    def test_single_keyword(self):
        label = generate_label(["inference"])
        assert label == "inference"


class TestBuildClusterDict:
    def test_required_keys_present(self):
        cluster = build_cluster_dict(
            topic_id=0,
            keywords=SAMPLE_KEYWORDS,
            centroid=SAMPLE_CENTROID,
            paper_ids=SAMPLE_PAPER_IDS,
            umap_x=2.34,
            umap_y=-1.12,
        )
        for key in ["id", "keywords", "label", "centroid", "paper_ids", "size", "umap_x", "umap_y"]:
            assert key in cluster, f"Missing key: {key}"

    def test_size_equals_paper_ids_length(self):
        cluster = build_cluster_dict(
            topic_id=1,
            keywords=SAMPLE_KEYWORDS,
            centroid=SAMPLE_CENTROID,
            paper_ids=SAMPLE_PAPER_IDS,
            umap_x=0.0,
            umap_y=0.0,
        )
        assert cluster["size"] == len(SAMPLE_PAPER_IDS)

    def test_id_matches_topic_id(self):
        cluster = build_cluster_dict(
            topic_id=42,
            keywords=SAMPLE_KEYWORDS,
            centroid=SAMPLE_CENTROID,
            paper_ids=SAMPLE_PAPER_IDS,
            umap_x=0.0,
            umap_y=0.0,
        )
        assert cluster["id"] == 42

    def test_centroid_is_list(self):
        cluster = build_cluster_dict(
            topic_id=0,
            keywords=SAMPLE_KEYWORDS,
            centroid=SAMPLE_CENTROID,
            paper_ids=SAMPLE_PAPER_IDS,
            umap_x=0.0,
            umap_y=0.0,
        )
        assert isinstance(cluster["centroid"], list)


class TestBuildMapOutput:
    def _sample_clusters(self):
        return [
            build_cluster_dict(
                topic_id=i,
                keywords=SAMPLE_KEYWORDS,
                centroid=SAMPLE_CENTROID,
                paper_ids=SAMPLE_PAPER_IDS,
                umap_x=float(i),
                umap_y=float(i),
            )
            for i in range(3)
        ]

    def test_required_keys_present(self):
        output = build_map_output(
            clusters=self._sample_clusters(),
            total_papers=100,
            model="allenai/specter2",
        )
        for key in ["generated_at", "total_papers", "model", "clusters"]:
            assert key in output, f"Missing key: {key}"

    def test_total_papers(self):
        output = build_map_output(
            clusters=self._sample_clusters(),
            total_papers=9999,
            model="allenai/specter2",
        )
        assert output["total_papers"] == 9999

    def test_clusters_count(self):
        clusters = self._sample_clusters()
        output = build_map_output(clusters=clusters, total_papers=100, model="allenai/specter2")
        assert len(output["clusters"]) == len(clusters)
