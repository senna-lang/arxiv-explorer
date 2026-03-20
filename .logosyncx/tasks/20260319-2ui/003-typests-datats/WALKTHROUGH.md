## Key Specification

`src/lib/types.ts` に `SerendipityPaper` 型エイリアスと `RecommendationsData` の拡張フィールドを追加。

## What Was Done

- `SerendipityPaper = Recommendation` 型エイリアスを追加
- `RecommendationsData` に `serendipity_clusters?: TopCluster[]` と `serendipity?: SerendipityPaper[]` を追加（optional で後方互換性維持）
- `npx tsc --noEmit` でエラーなし確認

## How It Was Done

既存の `Recommendation` 型をエイリアスとして再利用することで、構造の重複を避けつつ意味的な区別を表現。

## Gotchas & Lessons Learned

optional フィールドにすることで、古い `recommendations.json`（セレンディピティフィールドなし）でも型エラーにならない。

## Reusable Patterns

特になし。
