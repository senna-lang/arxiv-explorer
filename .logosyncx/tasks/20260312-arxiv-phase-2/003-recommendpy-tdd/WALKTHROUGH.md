## Key Specification

recommend.pyをTDDで実装。instance-based scoring + α加重合成。

## What Was Done

- `scripts/tests/test_recommend.py`: 15テスト（Red→Green）
- `scripts/recommend.py`: compute_instance_score / compute_alpha / compute_final_score / rank_clusters / main を実装

## How It Was Done

各関数を独立してテスト。rank_clustersはscore フィールドを追加して降順ソートして返す。

## Gotchas & Lessons Learned

- rank_clustersはクラスタdictに`score`フィールドを追加して返すため、テストで`"score" in ranked[0]`を確認
- arXiv APIのid_list上限を考慮して100件に制限

## Reusable Patterns

```python
# α加重合成
alpha = min(1.0, n_ratings / 50)
final = alpha * instance_score + (1 - alpha) * profile_score
```
