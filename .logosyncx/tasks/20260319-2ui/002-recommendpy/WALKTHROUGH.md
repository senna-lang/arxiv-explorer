## Key Specification

recommend.py を拡張し、ランク4-6クラスタからスコアバンド [0.45, 0.65] の論文を「セレンディピティ」として抽出する。

## What Was Done

- `select_serendipity_papers()` 純粋関数を追加（スコアバンドフィルタ + 重複排除 + top_n）
- `main()` 内で `ranked[top_clusters:top_clusters+ser_n_clusters]` をセレンディピティクラスタとして選択
- 各セレンディピティクラスタから arxiv API で論文取得 → embed → cosine sim 計算
- `output` dict に `serendipity_clusters` / `serendipity` フィールドを追加
- datamapplot のセレンディピティクラスタを `#10b981`（緑）でハイライト
- `scripts/test_recommend.py` に8件のユニットテストを追加（全パス）

## How It Was Done

既存の recommendations ループと同じパターンで実装し、最後に `select_serendipity_papers()` で一括フィルタリング。

## Gotchas & Lessons Learned

テスト実行は `scripts/` ディレクトリ内で `python -m pytest test_recommend.py` とする（プロジェクトルートからだと `recommend` モジュールが見つからない）。

## Reusable Patterns

純粋関数 `select_serendipity_papers(papers, min_score, max_score, top_n, exclude_ids)` は他のフィルタリングにも流用できる。
