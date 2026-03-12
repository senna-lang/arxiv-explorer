## Key Specification

RecommendSection.astroを実装。recommendations.jsonを読み込み近傍クラスタとおすすめ論文を表示。

## What Was Done

- `src/lib/types.ts`にCluster/MapData/Recommendation/TopCluster/RecommendationsData型を追加
- `src/lib/data.ts`にgetMap() / getRecommendations()を追加
- `src/components/RecommendSection.astro`を実装（データなし時は非表示）

## How It Was Done

AstroのフロントマターでgetRecommendations()を呼び、nullまたは空配列なら何も描画しない。
クラスタタグはblue、近傍クラスタはハイライト表示。

## Reusable Patterns

```astro
// データなし時に丸ごと非表示
{data && data.recommendations.length > 0 && (
  <section>...</section>
)}
```
