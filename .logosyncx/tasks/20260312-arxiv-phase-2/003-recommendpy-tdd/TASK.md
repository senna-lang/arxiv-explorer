---
id: t-40a4b0
date: 2026-03-12T10:31:00.622613+09:00
title: recommend.py TDD実装
seq: 3
status: done
priority: medium
plan: 20260312-arxiv-phase-2
tags: []
assignee: ""
completed_at: 2026-03-12T10:42:35.963492+09:00
---

## What

`scripts/recommend.py`をTDDで実装する。ratings.jsonとmap.jsonから
instance-based scoringでおすすめ論文を生成しrecommendations.jsonに保存する。

## Why

ratings蓄積の成果を「おすすめ」として還元するPhase 2のゴール。

## Scope

- `scripts/recommend.py`
- `scripts/tests/test_recommend.py`

## Acceptance Criteria

- [ ] `python -m pytest scripts/tests/test_recommend.py -v`が全テストPASS
- [ ] `python scripts/recommend.py`でdata/recommendations.jsonが生成される
- [ ] スコア計算が仕様通り（instance_score + profile_score の加重合成）

## Checklist

- [ ] `scripts/tests/test_recommend.py`を先に書く（Red）
  - [ ] `test_compute_instance_score`: centroidと複数rated_vecsのcos類似度平均
  - [ ] `test_compute_alpha`: ratings件数に応じたα計算（0件=0.0、50件=1.0）
  - [ ] `test_compute_final_score`: α加重合成の検証
  - [ ] `test_rank_clusters`: スコア降順ソート
- [ ] `scripts/recommend.py`を実装（Green）
  - [ ] `compute_instance_score(centroid, rated_vecs) -> float`
  - [ ] `compute_alpha(n_ratings) -> float`: min(1.0, n/50)
  - [ ] `compute_final_score(instance, profile, alpha) -> float`
  - [ ] `rank_clusters(clusters, rated_vecs, profile_vecs, alpha) -> list`
  - [ ] `main(top_clusters, top_n)`: 全体フロー
- [ ] `python -m pytest scripts/tests/ -v`でPASS確認

## Notes

- instance-based scoring: 各高評価論文が独立に投票 → 多峰性の興味を自然に扱える
- ratings 0件でも動作（α=0なのでprofile_scoreのみで推薦）
- embeddings再計算（ratings.jsonにはembeddingを保存しない）
