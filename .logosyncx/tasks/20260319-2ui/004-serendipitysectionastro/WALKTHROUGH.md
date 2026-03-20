## Key Specification

`SerendipitySection.astro` を新規作成し、緑系カラースキームでセレンディピティ論文を表示。

## What Was Done

- `src/components/SerendipitySection.astro` を新規作成
- `RecommendSection.astro` をベースに、タイトル・ラベル・カラースキームを変更
- `RecommendSection.astro` の `.recommend-section` から `margin-top` / `border-top` を削除（親制御へ移行）

## How It Was Done

`data.serendipity` / `data.serendipity_clusters` が空/未定義のときは何も表示しない条件付きレンダリング。

## Gotchas & Lessons Learned

`data.serendipity!.map(...)` の non-null assertion は `hasPapers` チェック後なので安全。

## Reusable Patterns

特になし。
