---
id: t-4d9d3b
date: 2026-03-12T10:31:00.628865+09:00
title: RecommendSection実装
seq: 4
status: done
priority: medium
plan: 20260312-arxiv-phase-2
tags: []
assignee: ""
completed_at: 2026-03-12T10:46:47.507149+09:00
---

## What

Phase 1でstubだった`RecommendSection.astro`を実装する。
recommendations.jsonを読み込み、近傍クラスタとおすすめ論文カードを表示する。

## Why

recommend.pyの出力をUIに反映するフロントエンド側の実装。

## Scope

- `src/components/RecommendSection.astro`
- `src/lib/data.ts`（getRecommendations()を追加）
- `src/lib/types.ts`（Recommendation型を追加）

## Acceptance Criteria

- [ ] recommendations.jsonがあれば近傍クラスタ名とスコアが表示される
- [ ] おすすめ論文がPaperCard相当のUIで表示される（マッチ度付き）
- [ ] recommendations.jsonがなければセクション自体が非表示

## Checklist

- [ ] `src/lib/types.ts`にRecommendation/RecommendationsData型を追加
- [ ] `src/lib/data.ts`に`getRecommendations()`を追加
- [ ] `src/components/RecommendSection.astro`を実装
  - [ ] top_clusters（クラスタ名 + スコア%）の表示
  - [ ] 論文リスト（タイトル/URL/マッチ度/abstract展開）
  - [ ] データなし時は非表示
- [ ] `bun run build`でエラーなし確認

## Notes

- PaperCardを再利用してもよいが、レーティング機能は不要（閲覧のみ）
- matched_clusterをサブタイトルとして表示するとコンテキストが分かりやすい
