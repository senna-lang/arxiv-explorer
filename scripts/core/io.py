"""
JSONファイル入出力ユーティリティ

提供:
- save_json(path, data): JSONファイルを保存（ensure_ascii=False, indent=2）
- append_jsonl(path, entry): JSONLファイルに1行追記
"""

import json
from pathlib import Path
from typing import Any


def save_json(path: Path, data: Any) -> None:
    """data を JSON ファイルに保存する。"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def append_jsonl(path: Path, entry: Any) -> None:
    """entry を JSON Lines ファイルに1行追記する。"""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
