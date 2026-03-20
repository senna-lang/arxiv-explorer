"""
scripts/core/config.py のユニットテスト

テスト対象:
- load_config: config.jsonc をパースして辞書を返す
- ROOT, CONFIG_PATH, JST: 定数の正当性
"""

import os
import sys
import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config import CONFIG_PATH, JST, ROOT, load_config


class TestConstants:
    def test_jst_is_asia_tokyo(self):
        assert JST == ZoneInfo("Asia/Tokyo")

    def test_root_is_project_root(self):
        # ROOT は config.jsonc が存在する場所（リポジトリルート）を指す
        assert (ROOT / "config.jsonc").exists()

    def test_config_path_points_to_config_jsonc(self):
        assert CONFIG_PATH.name == "config.jsonc"
        assert CONFIG_PATH.exists()


class TestLoadConfig:
    def test_load_real_config(self):
        config = load_config()
        assert isinstance(config, dict)
        assert "embedding_model" in config
        assert "categories" in config

    def test_strips_line_comments(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonc", delete=False, encoding="utf-8"
        ) as f:
            f.write('{\n  // this is a comment\n  "key": "value"\n}\n')
            tmp_path = Path(f.name)
        try:
            from core.config import _load_jsonc

            result = _load_jsonc(tmp_path)
            assert result == {"key": "value"}
        finally:
            tmp_path.unlink()

    def test_strips_trailing_comma(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonc", delete=False, encoding="utf-8"
        ) as f:
            f.write('{\n  "key": "value",\n}\n')
            tmp_path = Path(f.name)
        try:
            from core.config import _load_jsonc

            result = _load_jsonc(tmp_path)
            assert result == {"key": "value"}
        finally:
            tmp_path.unlink()

    def test_preserves_strings_with_slashes(self):
        """コメント除去が文字列内の // を誤って除去しないことを確認"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonc", delete=False, encoding="utf-8"
        ) as f:
            f.write('{\n  "url": "https://example.com/path"\n}\n')
            tmp_path = Path(f.name)
        try:
            from core.config import _load_jsonc

            result = _load_jsonc(tmp_path)
            assert result == {"url": "https://example.com/path"}
        finally:
            tmp_path.unlink()
