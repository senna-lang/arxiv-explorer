---
id: t-a0d028
date: 2026-03-17T22:17:20.533027+09:00
title: map.py Modal 対応（10,000件・T4）
seq: 6
status: done
priority: high
plan: 20260315-
depends_on:
    - 3
tags: []
assignee: ""
completed_at: 2026-03-17T23:04:46.321108+09:00
---

## What

`scripts/map.py` を Modal T4 GPU 上で 10,000件フルで実行できるよう対応する。M2 24GB で ~20分かかる処理を T4 で ~15分に短縮。

## Why

月次バッチの最重量処理。10,000件の embedding + BERTopic クラスタリングを安定して実行するため Modal GPU を使う。

## Scope

- `scripts/map.py`（編集）
- `scripts/modal_app.py`（必要に応じて関数追加）

## Acceptance Criteria

- [ ] `modal run scripts/map.py` で `data/map.json`（10,000件）が生成される
- [ ] `python scripts/map.py`（ローカル実行）も引き続き動く
- [ ] T4 上で ~15分以内に完了する

## Checklist

- [ ] map.py の embedding 箇所と BERTopic 処理を確認
- [ ] embedding のみ Modal T4 に委譲（BERTopic はローカルでも動く）
- [ ] max_papers=10000 を デフォルトに変更（または `--max-papers` 引数で指定）
- [ ] `modal run scripts/map.py` で動作確認・時間計測

## Notes

- BERTopic 自体は CPU でも動くが、embedding が一番重い
- embedding を Modal で実行し、結果の numpy array を返してローカルで BERTopic に渡す設計が最もシンプル
- タイムアウト設定に注意（Modal のデフォルト timeout は 300秒 → `timeout=1800` に変更が必要）
