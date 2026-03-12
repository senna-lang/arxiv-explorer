## Key Specification

map.pyをTDDで実装。build_cluster_dict / generate_label / build_map_outputをユニットテスト済み。

## What Was Done

- `scripts/tests/test_map.py`: 11テスト（Red→Green）
- `scripts/map.py`: fetch_arxiv_papers / generate_label / build_cluster_dict / build_map_output / main を実装

## How It Was Done

BERTopicにUMAP（random_state=42固定）とHDBSCANを明示的に渡して再現性を確保。
ノイズクラスタ（topic_id=-1）はスキップ。

## Gotchas & Lessons Learned

- BERTopicのデフォルトUMAPはrandom_stateが固定されないため、明示的にUMAP(random_state=42)を渡す必要がある
- `pip install bertopic`でumap-learn・hdbscanも自動インストールされる

## Reusable Patterns

```python
# UMAPのrandom_state固定
from umap import UMAP
from hdbscan import HDBSCAN
topic_model = BERTopic(
    umap_model=UMAP(n_components=2, random_state=42, metric="cosine"),
    hdbscan_model=HDBSCAN(min_cluster_size=10, metric="euclidean", prediction_data=True),
)
# ノイズクラスタをスキップ
for topic_id in unique_topics:
    if topic_id == -1:
        continue
```
