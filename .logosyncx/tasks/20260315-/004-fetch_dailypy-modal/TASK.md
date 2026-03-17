---
id: t-62a284
date: 2026-03-17T22:17:14.40584+09:00
title: fetch_daily.py Modal 対応
seq: 4
status: done
priority: high
plan: 20260315-
depends_on:
    - 3
tags: []
assignee: ""
completed_at: 2026-03-17T23:04:46.301608+09:00
---

## What

`scripts/fetch_daily.py` の embedding 部分を `@modal.function(gpu="T4")` として切り出し、`modal run` でも手動実行でも動くようにする。

## Why

specter2_base の推論を Modal T4 GPU 上で実行することで、GitHub Actions の RAM 制約を回避する。

## Scope

- `scripts/fetch_daily.py`（編集）
- `scripts/modal_app.py`（embedding 関数を追加）

OUT of scope: GitHub Actions workflow（タスク 7）

## Acceptance Criteria

- [ ] `modal run scripts/fetch_daily.py` で `data/YYYYMMDD.json` が生成される
- [ ] `python scripts/fetch_daily.py`（ローカル実行）も引き続き動く
- [ ] T4 GPU で embedding が実行されることをログで確認できる

## Checklist

- [ ] `modal_app.py` に `encode_texts` 関数を `@modal.function(gpu="T4")` で定義
- [ ] `fetch_daily.py` の `enc.encode()` 呼び出しを Modal 関数経由に切り替え
- [ ] ローカル実行時は従来の `Specter2Encoder` を使うフォールバックを維持
- [ ] `modal run scripts/fetch_daily.py` で動作確認

## Notes

Modal 関数と既存コードの分離方針:
- `modal run` 実行時: embedding を Modal T4 上で実行
- `python` 直接実行時: 従来通りローカルで実行
- 環境判定は `modal.is_local()` または環境変数フラグで切り替え
