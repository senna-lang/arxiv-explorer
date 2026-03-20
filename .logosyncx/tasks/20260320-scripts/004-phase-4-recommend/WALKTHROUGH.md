## Key Specification

`scripts/recommend.py`（409行）を `scripts/recommend/` パッケージに分割。スコアリング数学・セレンディピティ・可視化を独立モジュール化。

## What Was Done

- `scripts/recommend/` パッケージ作成
  - `__init__.py` — main, compute_instance_score, compute_alpha, compute_final_score, rank_clusters, select_serendipity_papers を re-export
  - `cluster_ranking.py` — compute_instance_score(), compute_alpha(), compute_final_score(), rank_clusters(), fetch_papers_for_cluster()
  - `serendipity.py` — select_serendipity_papers()
  - `visualization.py` — regenerate_map_html()（color_map 付きハイライト）
  - `cli.py` — main() オーケストレーション + modal_main + argparse
- `scripts/recommend.py` を削除（git rm）
- 迷子テスト `scripts/test_recommend.py` を削除（git rm）
- 新テスト: test_recommend_ranking.py / test_recommend_serendipity.py（計20ケース）
- 旧 `scripts/tests/test_recommend.py` は `from recommend import ...` 経由で継続動作

## How It Was Done

TDDサイクル: 新テストファイル先行作成 → パッケージ作成 → 旧ファイル削除

## Gotchas & Lessons Learned

- compute_instance_score は Phase 1 の mean_cosine_similarity を使うだけになりシンプル化
- Modal の `@app.local_entrypoint()` 衝突（fetch_daily + map_pipeline + recommend が同名 modal_main を登録）により、複数パッケージを同一 pytest セッションで import するとエラー。グループ別実行で回避（既知問題）
- `scripts/test_recommend.py`（tests/ 外の迷子）は旧 recommend.py を直接 import していたため削除が必要だった

## Reusable Patterns

```python
# recommend パッケージの公開 API
from recommend import (
    compute_instance_score, compute_alpha, compute_final_score,
    rank_clusters, select_serendipity_papers, main
)
```
