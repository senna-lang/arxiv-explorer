## Key Specification

GitHub Actions と Modal の両環境で `pip install -r requirements.txt` が通ること。

## What Was Done

`requirements.txt` を新規作成。全スクリプトの import を確認して依存パッケージを列挙した。

## How It Was Done

`scripts/*.py` の import 文を grep して外部パッケージを特定:
- `adapters`, `transformers`: specter2.py が使用
- `arxiv`, `numpy`, `torch`, `sentence-transformers`: fetch_daily / recommend / map
- `bertopic`, `datamapplot`, `umap-learn`, `hdbscan`: map.py
- `modal`: Modal 対応タスク向けに追加

バージョン固定なし（`>=` 指定も省略）でシンプルに作成。

## Gotchas & Lessons Learned

- Modal 側では CUDA 版 torch を image 定義で別途インストールするため、requirements.txt の torch は CPU 版で問題ない
- `adapters` パッケージ（adapter-transformers）は pip 名が `adapters` なので注意

## Reusable Patterns

なし。
