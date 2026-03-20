"""
ratings データ取得ユーティリティ

提供:
- load_ratings(config, root): ratings_url(HTTP) またはローカルファイルから評価リストを返す
"""

import json
import urllib.request
from pathlib import Path
from typing import Any

from core.config import ROOT as _DEFAULT_ROOT


def load_ratings(
    config: dict[str, Any], root: Path = _DEFAULT_ROOT
) -> list[dict[str, Any]]:
    """
    ratings_urlが設定されていればHTTP(Cloudflare KV)、なければdata/ratings.jsonから読み込む。
    取得できない場合は空リストを返す。

    Args:
        config: load_config() の返り値
        root: リポジトリルートパス（テスト時に上書き可能）
    """
    ratings_url: str = config.get("ratings_url", "")
    output_dir = root / config["output_dir"]

    if ratings_url:
        try:
            with urllib.request.urlopen(ratings_url) as res:
                data = json.loads(res.read())
            return data.get("ratings", [])
        except Exception as e:
            print(f"[WARN] Failed to fetch ratings from {ratings_url}: {e}")

    ratings_path = output_dir / "ratings.json"
    if ratings_path.exists():
        with open(ratings_path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("ratings", [])

    print("[WARN] No ratings source available. Using profile-only scoring.")
    return []
