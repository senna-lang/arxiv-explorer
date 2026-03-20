---
id: t-80fdc9
date: 2026-03-19T22:43:15.778958+09:00
title: recommend.py にセレンディピティ抽出ロジックを実装
seq: 2
status: done
priority: high
plan: 20260319-2ui
tags: []
assignee: ""
completed_at: 2026-03-19T22:48:19.254988+09:00
---

## What

`scripts/recommend.py` を拡張し、ランク4-6クラスタから類似度バンド [0.45, 0.65] の論文を抽出する `select_serendipity_papers()` 純粋関数を実装し、`recommendations.json` に `serendipity` / `serendipity_clusters` フィールドを追加する。datamapplotのセレンディピティクラスタを緑色でハイライトする。

## Why

「こんなのもどう？」セクションのデータ源となる。直接の興味の隣接領域からの発見を促す。

## Scope

- `scripts/recommend.py`
- `scripts/test_recommend.py` (新規)

OUT: フロントエンド変更（タスク3-5で行う）

## Acceptance Criteria

- [ ] `select_serendipity_papers(papers_with_scores, min_score, max_score, top_n, exclude_ids)` が正しく動作する
- [ ] `recommendations.json` に `serendipity` と `serendipity_clusters` フィールドが存在する
- [ ] 重複論文（recommendations にも存在するID）が除外される
- [ ] ユニットテストがすべてパスする

## Checklist

- [ ] `select_serendipity_papers()` を純粋関数として抽出
- [ ] `main()` 内で ranked[top_clusters:top_clusters+ser_n] をセレンディピティクラスタとして選択
- [ ] 各クラスタで fetch_papers_for_cluster → encode → cosine sim → バンドフィルタ
- [ ] recommendations IDセットで重複排除
- [ ] output dict に serendipity フィールドを追加
- [ ] datamapplot のラベルカラーに `#10b981`（緑）を追加
- [ ] `scripts/test_recommend.py` にユニットテストを作成
  - スコアバンドフィルタのテスト
  - 重複排除のテスト
  - 空クラスタ（クラスタ数<4）のグレースフルデグレードテスト

## Notes

- `enc.encode()` は高コストなので、クラスタループ内での呼び出し回数に注意
- `fetch_papers_for_cluster` は arxiv API コールを含む（上限100件）
