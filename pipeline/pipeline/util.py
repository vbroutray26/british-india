"""Shared helpers: paths, hashing, YAML/JSON IO, structured logging, polite HTTP."""
from __future__ import annotations

import hashlib
import json
import logging
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

from pipeline import DATA_DIR, REPO_ROOT

RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
MANIFEST_DIR = DATA_DIR / "manifests"
CONFIG_DIR = REPO_ROOT / "pipeline" / "config"
USER_AGENT = "towns-of-british-india-pipeline/0.1 (+https://github.com/vbroutray26/british-india)"


def log(stage: str) -> logging.Logger:
    lg = logging.getLogger(stage)
    if not lg.handlers:
        h = logging.StreamHandler(sys.stderr)
        h.setFormatter(logging.Formatter(f"%(asctime)s {stage} %(levelname)s %(message)s", "%H:%M:%S"))
        lg.addHandler(h)
        lg.setLevel(logging.INFO)
    return lg


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


def read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text()) if path.exists() else None


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    """Deterministic JSON Lines (sorted keys) so reruns are byte-identical (TS-DATA-11)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    tmp.replace(path)  # atomic: a killed run never leaves a half-written file (TS-DATA-12)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def http_get(url: str, dest: Path | None = None, retries: int = 5, lg: logging.Logger | None = None) -> bytes | None:
    """GET with exponential backoff + jitter on 429/5xx/timeouts (spec §9.4 'never hammer')."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as r:
                if dest is None:
                    return r.read()
                tmp = dest.with_suffix(dest.suffix + ".part")
                dest.parent.mkdir(parents=True, exist_ok=True)
                with tmp.open("wb") as f:
                    while chunk := r.read(1 << 20):
                        f.write(chunk)
                tmp.replace(dest)
                return None
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == retries - 1:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == retries - 1:
                raise
        wait = min(60, 2 ** attempt) + random.random()
        if lg:
            lg.warning("retry %s in %.1fs: %s", attempt + 1, wait, url)
        time.sleep(wait)
    return None
