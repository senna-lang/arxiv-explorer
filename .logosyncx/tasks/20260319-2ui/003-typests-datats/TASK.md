---
id: t-f7339e
date: 2026-03-19T22:43:40.099416+09:00
title: types.ts と data.ts の型定義を拡張
seq: 3
status: done
priority: medium
plan: 20260319-2ui
tags: []
assignee: ""
completed_at: 2026-03-19T23:52:41.378592+09:00
---

## What

`src/lib/types.ts` に `SerendipityPaper` 型エイリアスを追加し、`RecommendationsData` に `serendipity_clusters?` / `serendipity?` フィールドを追加する。`data.ts` の変更は不要。

## Why

フロントエンドコンポーネントがセレンディピティデータを型安全に扱えるようにする。

## Scope

- `src/lib/types.ts`

OUT: `src/lib/data.ts`（`getRecommendations()` は型変更のみで対応可能）

## Acceptance Criteria

- [ ] `SerendipityPaper = Recommendation` 型エイリアスが存在する
- [ ] `RecommendationsData` に `serendipity_clusters?: TopCluster[]` が存在する
- [ ] `RecommendationsData` に `serendipity?: SerendipityPaper[]` が存在する
- [ ] `npx tsc --noEmit` がエラーなしでパスする

## Checklist

- [ ] `types.ts` に `SerendipityPaper` 型エイリアスを追加
- [ ] `RecommendationsData` を拡張（optional フィールドで後方互換性維持）
- [ ] `npx tsc --noEmit` で確認
