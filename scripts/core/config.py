"""
設定ファイル読み込みと共通定数

提供:
- JST: 日本標準時タイムゾーン
- ROOT: リポジトリルートパス
- CONFIG_PATH: config.jsonc のパス
- load_config(): config.jsonc を辞書として返す
- _load_jsonc(path): 任意の .jsonc ファイルをパースする（テスト用）
"""

import json
import re
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = ROOT / "config.jsonc"


def _load_jsonc(path: Path) -> dict[str, Any]:
    """
    .jsonc ファイルを読み込む。
    行コメント（// ...）と末尾カンマを除去してJSONパースする。
    文字列リテラル内の // は除去しない。
    """
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r'"[^"\\]*(?:\\.[^"\\]*)*"|//[^\n]*',
        lambda m: m.group(0) if m.group(0).startswith('"') else "",
        text,
    )
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return json.loads(text)


def load_config() -> dict[str, Any]:
    """config.jsonc を読み込んで辞書を返す。"""
    return _load_jsonc(CONFIG_PATH)
