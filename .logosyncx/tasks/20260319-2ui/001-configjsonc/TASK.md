---
id: t-a1fd03
date: 2026-03-19T22:42:46.16914+09:00
title: config.jsonc にセレンディピティ設定を追加
seq: 1
status: open
priority: medium
plan: 20260319-2ui
tags: []
assignee: ""
---

## What

`config.jsonc` の `recommendation` セクションにセレンディピティ用の4設定項目（`serendipity_clusters`, `serendipity_top_n`, `serendipity_min_match_score`, `serendipity_max_match_score`）を追加する。

## Why

recommend.py のセレンディピティロジックが参照するパラメータを外部化することで、スコアバンドのチューニングをコード変更なしで行えるようにする。

## Scope

- `config.jsonc`

OUT: recommend.py の実装変更（タスク2で行う）

## Acceptance Criteria

- [ ] `serendipity_clusters: 3` が存在する
- [ ] `serendipity_top_n: 10` が存在する
- [ ] `serendipity_min_match_score: 0.45` が存在する
- [ ] `serendipity_max_match_score: 0.65` が存在する

## Checklist

- [ ] `recommendation` セクション内の `min_match_score` 直後に4項目を追加
- [ ] JSONCとして構文的に正しいこと確認（末尾カンマ等）
