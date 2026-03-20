import sys
from pathlib import Path

# python -m scripts.X 実行時に scripts/ を sys.path に追加して modal_app 等を import 可能にする
sys.path.insert(0, str(Path(__file__).parent))
