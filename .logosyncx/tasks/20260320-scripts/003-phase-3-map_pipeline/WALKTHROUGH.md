## Key Specification

`scripts/map.py`（427行）を `scripts/map_pipeline/` パッケージに分割。stopwords/BERTopic設定を clustering.py に隔離し、可読性を大幅改善。

## What Was Done

- `scripts/map_pipeline/` パッケージ作成
  - `__init__.py` — main, generate_label, build_cluster_dict, build_map_output を re-export
  - `aggregation.py` — generate_label(), build_cluster_dict(), build_map_output()
  - `fetch.py` — fetch_arxiv_papers()（hashlib キャッシュ付き）
  - `clustering.py` — ACADEMIC_STOPWORDS + build_bertopic_model()（80行超のBERTopic設定を隔離）
  - `visualization.py` — generate_map_html()（datamapplot ラッパー）
  - `cli.py` — main() オーケストレーション + modal_main + argparse
- `scripts/map.py` を削除（git rm）
- テスト移行: test_map_aggregation.py を新規作成、旧 test_map.py は `from map_pipeline import ...` に更新

## How It Was Done

TDDサイクル: test_map_aggregation.py 先行作成 → パッケージ作成 → 旧ファイル削除

## Gotchas & Lessons Learned

- Modal の `@app.local_entrypoint()` が複数パッケージで同名 `modal_main` を登録すると、同一セッションで両パッケージを import した際に InvalidError が出る。テストは fetch_daily 系と map_pipeline/core 系を分けて実行する必要がある（既存の既知問題）
- `topic_model.umap_model` でfitずみのUMAPモデルにアクセスできる（元コードから保持）

## Reusable Patterns

```python
# visualization.py の label_color_map を省略するとデフォルト色
generate_map_html(umap_2d, paper_ids, topic_to_label, topics, html_path)

# recommend.py でハイライトするときは label_color_map を渡す
generate_map_html(..., label_color_map={"label": "#f59e0b"})
```
