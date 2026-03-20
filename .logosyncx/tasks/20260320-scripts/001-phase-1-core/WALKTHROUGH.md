## Key Specification

Phase 1: 3スクリプト（fetch_daily, map, recommend）に重複している共通コードを `scripts/core/` パッケージとして抽出する。振る舞い変更なし。

## What Was Done

- `scripts/core/__init__.py` 作成
- `scripts/core/config.py` — JST, ROOT, CONFIG_PATH, load_config(), _load_jsonc()
- `scripts/core/similarity.py` — cosine_similarity(), mean_cosine_similarity()
- `scripts/core/ratings.py` — load_ratings()（fetch_daily の堅牢版）
- `scripts/core/io.py` — save_json(), append_jsonl()
- `scripts/core/arxiv_client.py` — strip_version(), build_category_query()
- fetch_daily.py, map.py, recommend.py の重複定義を削除し core から import に置換
- テスト3ファイル追加: test_core_config.py, test_core_similarity.py, test_core_ratings.py（計21ケース）

## How It Was Done

TDDサイクル: テスト先行（Red）→ モジュール作成（Green）→ 既存スクリプト更新

## Gotchas & Lessons Learned

- `Path(__file__).parent.parent.parent` は pytest 実行時に相対パスになるケースがある。`.resolve()` を追加して絶対パスに固定する必要がある
- `test_map.py` / `test_recommend.py` が既存で modal の重複エントリポイントエラーを起こしているが、これは Phase 1 以前からの既知問題

## Reusable Patterns

```python
# core モジュールの import パターン
from core.config import JST, ROOT, load_config
from core.similarity import cosine_similarity, mean_cosine_similarity
from core.ratings import load_ratings
from core.io import save_json, append_jsonl
from core.arxiv_client import strip_version, build_category_query
```
