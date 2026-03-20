---
id: t-dd92df
date: 2026-03-20T12:35:39.842915+09:00
title: 'Phase 3: map_pipeline パッケージ化'
seq: 3
status: done
priority: medium
plan: 20260320-scripts
tags: []
assignee: ""
completed_at: 2026-03-20T21:23:48.815856+09:00
---

## What

`scripts/map.py`（427行）を `scripts/map_pipeline/` パッケージに分割。80行超のstopwords/BERTopic設定を clustering.py に隔離し、可読性を大幅改善。

## Why

最も行数が多いスクリプト。特にBERTopic設定ブロック（stopwords + パイプライン構築）が main() の中に埋もれており読みづらい。

## Scope

- `scripts/map.py` → 削除
- `scripts/map_pipeline/__init__.py` (新規)
- `scripts/map_pipeline/cli.py` (新規)
- `scripts/map_pipeline/fetch.py` (新規) — fetch_arxiv_papers() + cache
- `scripts/map_pipeline/clustering.py` (新規) — ACADEMIC_STOPWORDS, build_bertopic_model()
- `scripts/map_pipeline/aggregation.py` (新規) — generate_label(), build_cluster_dict(), build_map_output()
- `scripts/map_pipeline/visualization.py` (新規) — generate_map_html()
- `scripts/tests/test_map_aggregation.py` (移行)

OUT of scope: fetch_daily, recommend

## Acceptance Criteria

- [ ] `scripts/map_pipeline/` パッケージが存在し、旧 map.py は削除
- [ ] `python -m scripts.map_pipeline --max-papers 100` が動作する
- [ ] benchmark.py の `from map_pipeline import main` が動作する
- [ ] `pytest scripts/tests/` が全パス

## Checklist

- [ ] map_pipeline/ パッケージ作成
- [ ] clustering.py にstopwords + BERTopicパイプライン設定を隔離
- [ ] aggregation.py に集約ロジック
- [ ] visualization.py に datamapplot 生成
- [ ] テスト移行
- [ ] `pytest scripts/tests/` passes
