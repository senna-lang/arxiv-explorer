---
id: t-397dd8
date: 2026-03-17T22:17:17.693072+09:00
title: recommend.py Modal 対応
seq: 5
status: done
priority: high
plan: 20260315-
depends_on:
    - 3
tags: []
assignee: ""
completed_at: 2026-03-17T23:04:46.313868+09:00
---

## What

`scripts/recommend.py` の embedding 部分を Modal T4 GPU 上で実行できるよう対応する。

## Why

fetch_daily.py と同様、GitHub Actions ランナーの RAM 制約を回避するため。

## Scope

- `scripts/recommend.py`（編集）
- `scripts/modal_app.py`（必要に応じて関数追加）

## Acceptance Criteria

- [ ] `modal run scripts/recommend.py` で `data/recommendations.json` が生成される
- [ ] `python scripts/recommend.py`（ローカル実行）も引き続き動く

## Checklist

- [ ] recommend.py の embedding 箇所を確認
- [ ] modal_app.py の encode 関数を流用 or 追加
- [ ] `modal run scripts/recommend.py` で動作確認

## Notes

fetch_daily.py と embedding ロジックが共通のため、modal_app.py の関数を再利用できる想定。
