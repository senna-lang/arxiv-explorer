# arxiv-compass

SPECTER2 + BERTopic による arXiv 論文ディスカバリー — 埋め込みベースの検索とトピッククラスタリングで、日次の論文レコメンドを生成する。

---

## 全体の流れ

```
[日次] arXiv から直接新着論文を取得・スコアリング
                │
                ▼
        ┌───────────────────────────────────┐
        │  fetch_daily.py                   │
        │  arXiv API から新着論文を取得     │
        │  → Embedding（SPECTER2）          │
        │  → interest_profile + ratings     │
        │    の α-blend でスコアリング      │
        │  → score 順に並べて data/ に保存  │
        └───────────────────────────────────┘
                │
                │  星をつけて評価を蓄積
                ▼
        Cloudflare KV
        ※ GET /api/ratings でバッチから参照
                │
                │
[月次]          ▼
        ┌───────────────────────────────────┐
        │  arXiv論文 10,000件を取得         │
        │  BERTopic でトピックモデリング    │
        │  → 論文地図（map.json）を生成     │
        └───────────────────────────────────┘
                │
                │
[週次]          ▼
        ┌───────────────────────────────────┐
        │  ratings.json × map.json          │
        │  → 自分の興味クラスタを特定           │
        │  → 近傍論文をおすすめ表示            │
        │  → 隣接クラスタをセレンディピティ      │
        │    として表示                       │
        └───────────────────────────────────┘
```

---

## トピックモデリングの仕組み

```
10,000件の論文 abstract
        │
        ▼
  [STEP 1] Embedding（SPECTER2 + proximity アダプタ）
  各 abstract を 768 次元ベクトルに変換
        │
        ▼
  [STEP 2] PCA（768次元 → 50次元）
  ノイズ次元を落とし UMAP の入力品質を上げる
        │
        ▼
  [STEP 3] UMAP（50次元 → 2次元）
  クラスタリングと可視化を同一空間で統一
  ※ 「地図上の近さ」と「クラスタの近さ」が一致する
        │
        ▼
  [STEP 4] HDBSCAN でクラスタリング
  密度ベースでグループを自動検出（クラスタ数は自動決定）
        │
        ▼
  [STEP 5] c-TF-IDF でキーワード候補抽出
  各クラスタを代表する語を統計的に抽出
  ※ WordNetLemmatizer で語形正規化（agents → agent、rewards → reward）
  ※ ACADEMIC_STOPWORDS で論文特有の汎用語を除去
        │
        ▼
  [STEP 6] KeyBERTInspired で意味的再ランキング
  各クラスタの代表文書とキーワード候補を SPECTER2 で Embedding し、
  cos 類似度でスコアリング（10,000件の全論文は再 Embedding しない）
        │
        ▼
  [STEP 7] MaximalMarginalRelevance（MMR）で多様性確保
  選択済みキーワードとの意味的類似度を考慮し、
  概念的に近いペア（gnn / graph neural network 等）を除去して多様なキーワードに絞る
        │
        ▼
  map.json（arXiv論文地図）
  ┌─────────────────────────────────────┐
  │  cluster: "rlvr & policy optimization & grpo"      │
  │  cluster: "whisper & tts & asr"                    │
  │  cluster: "jailbreak & adversarial"                │
  │  cluster: "fine tuning & lora & rank adaptation"   │
  │  ...（数十クラスタ）                               │
  └─────────────────────────────────────┘
```

### 地図から「自分の興味領域」を発見する

```
Cloudflare KV
（星をつけた論文の abstract）
        │
        ▼
  評価済み論文が属するクラスタを特定
        │
        ▼
  高評価クラスタの centroid ベクトルを計算
        │
        ▼
  地図上の近傍クラスタを探索
  ┌──────────────────────────────────────────────────────┐
  │  "Diffusion Models" ← よく星をつけている            │
  │         ↓ 近い                                       │
  │  "Score-based Generative Models" ← まだ知らなかった │
  │  "Flow Matching" ← まだ知らなかった                 │
  └──────────────────────────────────────────────────────┘
        │
        ▼
  recommendations.json に2種類の論文リストを生成:
  - おすすめ（上位3クラスタの代表論文 7件）         → 🔍 過去記事からのおすすめ
  - こんなのもどう？（隣接3クラスタ 7件 + 末尾2クラスタ 3件）→ 🌱 こんなのもどう？
```

---

## スコアリングの仕組み

デイリー・おすすめ・こんなのもどう？ のすべてで同じ α-blend スコアを使用。

```
α = min(1.0, ratings件数 / 50)
match_score = α × cos_sim(論文, 高評価論文群) + (1-α) × cos_sim(論文, interest_profile)
```

ratings が少ない初期は interest_profile との類似度が主、
蓄積されるにつれて実際の評価データとの類似度が主になる。

`config.jsonc` の `interest_profile` に興味領域を自然言語で記述する（7項目）。

### SPECTER2 アダプタの使い分け

| アダプタ | 用途 |
|---|---|
| `proximity` | 論文同士の類似度（abstract の Embedding） |
| `adhoc_query` | クエリ→論文の検索（interest_profile の Embedding） |
