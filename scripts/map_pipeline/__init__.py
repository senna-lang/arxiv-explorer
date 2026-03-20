"""
map_pipeline パッケージ — arXiv論文クラスタリングパイプライン

主なエントリポイント:
- main(max_papers, log): fetch → embed → cluster → aggregate → save の一連の処理
"""

from .aggregation import build_cluster_dict, build_map_output, generate_label
from .cli import main

__all__ = ["main", "generate_label", "build_cluster_dict", "build_map_output"]
