## Key Specification

config.jsonのembedding_modelをall-MiniLM-L6-v2からallenai/specter2に変更。

## What Was Done

- `config.json`の`embedding_model`を`"allenai/specter2"`に変更（1行のみ）

## How It Was Done

parse.pyはconfig.jsonからモデル名を読み込むため本体変更不要。

## Gotchas & Lessons Learned

- 既存data/YYYYMMDD.jsonはall-MiniLM-L6-v2製なので、Phase 2移行後はparse.pyを再実行して再生成する必要がある

## Reusable Patterns

なし（設定変更のみ）
