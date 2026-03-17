## Key Specification

map.py を Modal T4 で 10,000件フル実行できるようにする。デフォルト max_papers=10000。

## What Was Done

- `map.py` の import と `enc = Specter2Encoder(model_name)` を `build_encoder` に置き換え（2行の変更のみ）
- `--max-papers` のデフォルトはすでに 10000 になっていた（変更不要）

## How It Was Done

fetch_daily / recommend と同じパターン。`_Specter2Backend.embed_documents()` は `enc.encode()` を呼ぶため、`enc` が `ModalEncoder` になっていれば自動的に Modal 経由になる。

## Gotchas & Lessons Learned

- BERTopic の内部で `_Specter2Backend.embed_documents()` が呼ばれる（KeyBERTInspired のキーワード抽出時）。これも Modal 経由になるが、BERTopic が呼ぶテキスト数は少ないので問題なし
- Modal の `@app.cls` タイムアウトは 1800秒（30分）に設定済み。10,000件の embedding は T4 で ~15分の見込みなので余裕あり
- `modal_app.py` の `timeout=1800` 設定が重要（デフォルト 300秒では OOM になる前にタイムアウトする）

## Reusable Patterns

fetch_daily.py と同じパターン（WALKTHROUGH 参照）。
