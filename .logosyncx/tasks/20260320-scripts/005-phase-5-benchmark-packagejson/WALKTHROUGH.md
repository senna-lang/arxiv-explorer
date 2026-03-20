## Key Specification

benchmark.py の import 先更新、package.json のスクリプトコマンド更新、全体の動作確認。

## What Was Done

**benchmark.py:**
- `from zoneinfo import ZoneInfo` + inline JST 定数 → `from core.config import JST, load_config`
- `run_recommend()` のインライン JSONC パース（15行）→ `load_config()` 1行
- `from map import main` → `from map_pipeline import main`
- ヘッダー文字列も `.py` 表記を除去

**package.json:**
- `python scripts/map.py` → `python -m scripts.map_pipeline`
- `python scripts/recommend.py` → `python -m scripts.recommend`
- `python scripts/fetch_daily.py` → `python -m scripts.fetch_daily`

## How It Was Done

benchmark.py の変更は最小限（インライン JSONC パースの削除と import 2箇所の更新のみ）。

## Gotchas & Lessons Learned

- `json` モジュールは `_last_entry()` でまだ使用しているため import を保持
- `scripts/__init__.py` は既存であるため `python -m scripts.X` は追加作業なしで動作する

## Reusable Patterns

```bash
# パッケージ化後の実行コマンド
python -m scripts.fetch_daily [--date YYYYMMDD] [--log]
python -m scripts.map_pipeline [--max-papers N] [--log]
python -m scripts.recommend [--top-clusters N] [--top-n N] [--log]
```
