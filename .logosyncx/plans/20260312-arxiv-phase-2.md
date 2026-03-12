---
id: 28b2f3
topic: arXiv新聞アプリ Phase 2実装
tags: []
agent: ""
related: ["20260311-arxiv-phase-1"]
tasks_dir: .logosyncx/tasks/20260312-arxiv-phase-2
distilled: false
---

## Background

Phase 1でratings.jsonへの評価蓄積基盤ができた。
Phase 2ではarXiv論文群をBERTopicで地図化し、ratings履歴から近傍クラスタを推定して
おすすめ論文を自動生成する。ratings 20件以上で本領を発揮する。

## Spec

### scripts/map.py（月次）
1. arXiv APIでcs.CL/cs.LG/cs.AI/cs.CR の過去N件（デフォルト10,000件）を取得
2. abstractをallenai/specter2でEmbedding
3. BERTopicでトピック抽出（UMAP random_state=42、HDBSCAN、c-TF-IDF）
4. 各クラスタのcentroid・UMAP 2D座標・キーワードを集約
5. data/map.jsonに保存

### scripts/recommend.py（週次）
1. ratings.jsonからrating>=2の論文を抽出
2. abstractをspecter2でEmbedding（再計算）
3. map.jsonの各クラスタをinstance-based scoringで評価
   `score(c) = mean(cos_sim(centroid_c, v_i) for v_i in rated_vecs)`
4. ratings件数に応じてinterest_profileスコアと加重合成
   `α = min(1.0, 件数/50)`
   `final = α * instance_score + (1-α) * profile_score`
5. 上位クラスタ内の論文をスコアリングしてrecommendations.jsonに保存

### Astroフロントエンド
- `src/pages/map.astro`: UMAPの2D座標でクラスタを散布図表示（Canvas/SVG）
- `src/components/RecommendSection.astro`: recommendations.jsonを読んで表示

## Key Decisions

Decision: Embeddingモデルをspecter2に統一。Rationale: map.py・recommend.pyで同一ベクトル空間を使う必要がある。parse.pyもspecter2に変更する（config.jsonのembedding_model更新のみ）。

Decision: クラスタの安定識別子はlabel（キーワード文字列）。Rationale: 月次再生成でtopic_idは変わりうる。labelはキーワードベースで意味的に安定。

Decision: map.astroの描画はCanvas（vanilla JS）。Rationale: D3等の外部ライブラリを避けてシンプルに保つ。

## Notes

- BERTopicはUMAP・HDBSCANを内包するため個別インストール不要
- 初回のspecter2 Embeddingは10,000件で数十分かかる
- Phase 3: ratings 50件以上でratings自体をHDBSCANでクラスタリングし興味ペルソナを自動分離
