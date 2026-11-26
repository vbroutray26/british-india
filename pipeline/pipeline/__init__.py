"""Towns of British India data pipeline. Stages DP-00..DP-16 live in sub-packages (spec §8)."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
SCHEMA_DIR = REPO_ROOT / "packages" / "schema" / "schemas"
