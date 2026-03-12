---
id: t-f6cba1
date: 2026-03-12T10:31:00.61634+09:00
title: map.py TDD実装
seq: 2
status: done
priority: medium
plan: 20260312-arxiv-phase-2
tags: []
assignee: ""
completed_at: 2026-03-12T10:39:55.78544+09:00
---

## What

`scripts/map.py`をTDDで実装する。arXiv APIで論文を大量取得しBERTopicでクラスタリング、
data/map.jsonを生成する。

## Why

arXiv論文群の「地図」がないとrecommend.pyが動かない。Phase 2の核心。

## Scope

- `scripts/map.py`
- `scripts/tests/test_map.py`

## Acceptance Criteria

- [ ] `python -m pytest scripts/tests/test_map.py -v`が全テストPASS
- [ ] `python scripts/map.py --max-papers 100`でdata/map.jsonが生成される（テスト用小規模）
- [ ] map.jsonがSPEC.mdのスキーマに準拠（generated_at/total_papers/model/clusters）
- [ ] 各クラスタにid/keywords/label/centroid/paper_ids/size/umap_x/umap_yが含まれる

## Checklist

- [ ] `scripts/tests/test_map.py`を先に書く（Red）
  - [ ] `test_build_cluster_dict`: クラスタdictのスキーマ検証
  - [ ] `test_generate_label`: keywordsからlabelを生成
  - [ ] BERTopic・arXiv APIはMockで差し替え
- [ ] `scripts/map.py`を実装（Green）
  - [ ] `fetch_arxiv_papers(categories, max_papers) -> list`: arXiv API取得
  - [ ] `build_cluster_dict(topic_id, keywords, centroid, paper_ids, umap_xy) -> dict`
  - [ ] `generate_label(keywords: list[str]) -> str`: 先頭キーワードを結合
  - [ ] `main(max_papers)`: BERTopicパイプライン全体
- [ ] `python -m pytest scripts/tests/ -v`でPASS確認

## Notes

- BERTopic依存: `bertopic>=0.16.0`（UMAP/HDBSCANを内包）
- UMAPはrandom_state=42で固定（再現性確保）
- クラスタIDは内部参照のみ、labelを安定識別子として使う
- `--max-papers 100`でテスト実行可能にすること
