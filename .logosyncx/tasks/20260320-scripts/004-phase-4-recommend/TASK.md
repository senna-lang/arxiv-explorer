---
id: t-8804fa
date: 2026-03-20T12:35:57.759739+09:00
title: 'Phase 4: recommend パッケージ化'
seq: 4
status: done
priority: medium
plan: 20260320-scripts
tags: []
assignee: ""
completed_at: 2026-03-20T21:45:42.152712+09:00
---

## What

`scripts/recommend.py`（409行）を `scripts/recommend/` パッケージに分割。スコアリング数学・セレンディピティ・可視化を独立モジュール化。

## Why

クラスタランキング・セレンディピティ選択・datamapplot再レンダリングという3つの異なる責務が混在。

## Scope

- `scripts/recommend.py` → 削除
- `scripts/recommend/__init__.py` (新規)
- `scripts/recommend/cli.py` (新規)
- `scripts/recommend/cluster_ranking.py` (新規) — compute_instance_score(), compute_alpha(), rank_clusters()
- `scripts/recommend/serendipity.py` (新規) — select_serendipity_papers()
- `scripts/recommend/visualization.py` (新規) — regenerate_map_html()
- `scripts/test_recommend.py` → `scripts/tests/test_recommend_serendipity.py` に移動
- `scripts/tests/test_recommend.py` → `scripts/tests/test_recommend_ranking.py` にリネーム

OUT of scope: fetch_daily, map_pipeline

## Acceptance Criteria

- [ ] `scripts/recommend/` パッケージが存在し、旧 recommend.py は削除
- [ ] `python -m scripts.recommend` が動作する
- [ ] benchmark.py の `from recommend import main` が動作する
- [ ] 迷子の `scripts/test_recommend.py` が `tests/` に統合されている
- [ ] `pytest scripts/tests/` が全パス

## Checklist

- [ ] recommend/ パッケージ作成
- [ ] cluster_ranking.py に純粋スコアリング関数
- [ ] serendipity.py にセレンディピティ選択
- [ ] visualization.py に map.html 再レンダリング
- [ ] 迷子テスト移動 + 既存テストリネーム
- [ ] `pytest scripts/tests/` passes
