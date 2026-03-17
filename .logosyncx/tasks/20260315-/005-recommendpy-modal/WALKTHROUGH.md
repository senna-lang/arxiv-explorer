## Key Specification

fetch_daily.py と同様、build_encoder() で Modal / ローカルを切り替える。

## What Was Done

`recommend.py` の import と `enc = Specter2Encoder(model_name)` を `build_encoder` に置き換え（2行の変更のみ）。

## How It Was Done

fetch_daily.py と全く同じパターン。`enc.encode()` の呼び出し箇所は変更不要。

## Gotchas & Lessons Learned

`recommend.py` は `enc` を3回使う（rated papers / profile / cluster papers）。Modal 経由の場合は毎回 `.remote()` が呼ばれるが、`@app.cls` の同一コンテナが再利用されるためモデルロードは初回のみ。

## Reusable Patterns

fetch_daily.py と同じパターン（WALKTHROUGH 参照）。
