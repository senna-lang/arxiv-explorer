"""
scripts/map_pipeline/aggregation.py のユニットテスト

テスト対象:
- generate_label: keywords からラベル文字列を生成
- build_cluster_dict: クラスタ dict のスキーマ検証
- build_map_output: map.json 全体のスキーマ検証
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from map_pipeline.aggregation import build_cluster_dict, build_map_output, generate_label

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
        assert generate_label([]) == "unknown"

    def test_single_keyword(self):
        assert generate_label(["inference"]) == "inference"


class TestBuildClusterDict:
    def test_required_keys_present(self):
        cluster = build_cluster_dict(0, SAMPLE_KEYWORDS, SAMPLE_CENTROID, SAMPLE_PAPER_IDS, 2.34, -1.12)
        for key in ["id", "keywords", "label", "centroid", "paper_ids", "size", "umap_x", "umap_y"]:
            assert key in cluster, f"Missing key: {key}"

    def test_size_equals_paper_ids_length(self):
        cluster = build_cluster_dict(1, SAMPLE_KEYWORDS, SAMPLE_CENTROID, SAMPLE_PAPER_IDS, 0.0, 0.0)
        assert cluster["size"] == len(SAMPLE_PAPER_IDS)

    def test_id_matches_topic_id(self):
        cluster = build_cluster_dict(42, SAMPLE_KEYWORDS, SAMPLE_CENTROID, SAMPLE_PAPER_IDS, 0.0, 0.0)
        assert cluster["id"] == 42

    def test_centroid_is_list(self):
        cluster = build_cluster_dict(0, SAMPLE_KEYWORDS, SAMPLE_CENTROID, SAMPLE_PAPER_IDS, 0.0, 0.0)
        assert isinstance(cluster["centroid"], list)


class TestBuildMapOutput:
    def _sample_clusters(self):
        return [
            build_cluster_dict(i, SAMPLE_KEYWORDS, SAMPLE_CENTROID, SAMPLE_PAPER_IDS, float(i), float(i))
            for i in range(3)
        ]

    def _sample_papers(self):
        return [
            {"id": "2503.00001", "umap_x": 0.1, "umap_y": 0.2, "cluster_id": 0},
            {"id": "2503.00002", "umap_x": 0.3, "umap_y": 0.4, "cluster_id": 1},
        ]

    def test_required_keys_present(self):
        output = build_map_output(self._sample_clusters(), self._sample_papers(), 100, "allenai/specter2")
        for key in ["generated_at", "total_papers", "model", "clusters", "papers"]:
            assert key in output, f"Missing key: {key}"

    def test_total_papers(self):
        output = build_map_output(self._sample_clusters(), self._sample_papers(), 9999, "allenai/specter2")
        assert output["total_papers"] == 9999

    def test_clusters_count(self):
        clusters = self._sample_clusters()
        output = build_map_output(clusters, self._sample_papers(), 100, "allenai/specter2")
        assert len(output["clusters"]) == len(clusters)
