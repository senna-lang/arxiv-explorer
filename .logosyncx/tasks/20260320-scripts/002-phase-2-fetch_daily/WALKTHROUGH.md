## Key Specification

`scripts/fetch_daily.py`（335行）を `scripts/fetch_daily/` パッケージに分割。fetch/dedup/scoring を独立モジュール化し、cli.py をオーケストレーション専用にする。

## What Was Done

- `scripts/fetch_daily/` パッケージ作成
  - `__init__.py` — main, deduplicate, load_seen_ids, score_papers を re-export
  - `dedup.py` — load_seen_ids(), deduplicate()
  - `fetch.py` — fetch_recent_papers()（core.arxiv_client を活用）
  - `scoring.py` — score_papers()（core.similarity.mean_cosine_similarity を活用）
  - `cli.py` — main() オーケストレーション + modal_main + argparse
- `scripts/fetch_daily.py` を削除（git rm）
- テスト移行: test_fetch_daily_dedup.py / test_fetch_daily_scoring.py として分離
- 旧 test_fetch_daily.py は `from fetch_daily import ...` が __init__.py 経由で動作し続けることを確認

## How It Was Done

TDDサイクル: 新テストファイル作成（Red）→ パッケージ作成（Green）→ 旧ファイル削除

## Gotchas & Lessons Learned

- `git rm -f` が必要（ローカル変更があるため）
- scoring.py は Phase 1 で作った `mean_cosine_similarity` を直接使えたため、コードが大幅にシンプルになった（ループ削除）
- `from fetch_daily import main` （benchmark.py）が `__init__.py` の re-export で引き続き動く

## Reusable Patterns

```python
# パッケージの __init__.py で後方互換 re-export
from .cli import main
from .dedup import deduplicate, load_seen_ids
from .scoring import score_papers
```
