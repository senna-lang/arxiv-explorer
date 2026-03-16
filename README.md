# arxiv-compass

SPECTER2 + BERTopic を用いた arXiv 論文探索 — 埋め込み品質、トピックの一貫性、スコアリング挙動を検証・調整するためのRepo

---

## 検証課題

1. **スコアリングは自分の興味を正しく捉えているか** —
  interest_profile の定義と ratings の蓄積が組み合わさって、実際に読みたい論文を上位に持ってくるか
2. **地図は信頼できるか** —
  クラスタが意味的に整合していて、「このクラスタの隣を探索する」という行動が有効か

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
        │  → interest_profile との類似度    │
        │  → score 順に並べて data/ に保存  │
        └───────────────────────────────────┘
                │
                │  星をつけて評価を蓄積
                ▼
        Cloudflare KV（星評価ストア）
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
        │  → 自分の興味クラスタを特定       │
        │  → 近傍論文をおすすめ表示         │
        └───────────────────────────────────┘
```

---

## コマンド

```bash
# フロントエンド
npm run dev          # 開発サーバー起動
npm run build        # 本番ビルド
npm run preview      # ビルド結果をプレビュー

# Pythonパイプライン
npm run daily        # 新着論文をスコアリングして data/YYYYMMDD.json を生成
npm run map          # 論文地図を生成（max 1000件）
npm run map:full     # 論文地図を生成（max 10000件）
npm run recommend    # おすすめ論文を生成

# KVへのデータ移行
npx wrangler kv key put "ratings" --namespace-id=797a1d2d28ef40cd86bb25c2bce60fe9 --path=data/ratings.json --remote
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
  recommendations.json
  近傍クラスタから論文をおすすめ
```

---

## スコアリングの仕組み（日次）

`fetch_daily.py` が arXiv API から新着論文を取得し、`config.json` に書いた **interest_profile** との意味的近さでスコアをつける。

```
abstract → Embedding（SPECTER2 proximity）──┐
                                             ├─ cosine similarity × 7 → 平均 = score（0〜1）
interest_profile × 7 → Embedding（adhoc_query）─┘
```

`config.json` の `interest_profile` に興味領域を自然言語で書くだけで自動計算される。
評価データが蓄積するにつれ、profile ベースから実績ベースへ段階的に移行する。

```
α = min(1.0, ratings件数 / 50)
final_score = α × instance_score + (1-α) × profile_score
```

ratings が少ない初期は `profile_score` が補完し、
蓄積されるにつれて実際の評価データ（`instance_score`）が主役になる。

### SPECTER2 アダプタの使い分け

| アダプタ | 用途 |
|---|---|
| `proximity` | 論文同士の類似度（abstract の Embedding） |
| `adhoc_query` | クエリ→論文の検索（interest_profile の Embedding） |

---

## データの流れ

| ファイル | 内容 | 更新 |
|---|---|---|
| `data/YYYYMMDD.json` | 当日の論文 + スコア | 毎朝（`daily`） |
| `data/ratings.json` | 星評価履歴の初期データ（Cloudflare KVへの移行元） | - |
| `data/map.json` | arXiv 論文地図（クラスタ + UMAP 2D 座標） | 月次（`map:full`） |
| `data/recommendations.json` | 近傍クラスタからのおすすめ論文 | 週次（`recommend`） |
| `public/map.html` | datamapplot 生成のインタラクティブ地図 | 月次・週次 |
| `.cache/arxiv_YYYYMMDD_*.pkl` | arXiv API レスポンスのキャッシュ | 自動 |
