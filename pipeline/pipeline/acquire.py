"""DP-00 Acquire (spec §8.1).

Downloads a source's scan and existing OCR from its host, verifies checksums against the host,
records SHA-256 in a public manifest, and never overwrites a raw file (a changed upstream file is
stored as a new version).

Usage: python -m pipeline.acquire --source omalley-puri-1908
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from pipeline.util import (
    CONFIG_DIR,
    MANIFEST_DIR,
    RAW_DIR,
    http_get,
    log,
    md5_file,
    read_yaml,
    sha256_file,
    write_json,
)

LG = log("DP-00")
IA = "https://archive.org"


def plan(identifier: str, cfg: dict) -> tuple[dict, list[dict]]:
    meta = json.loads(http_get(f"{IA}/metadata/{identifier}", lg=LG))
    wanted = []
    for f in meta.get("files", []):
        name = f["name"]
        if any(name.endswith(x) for x in cfg["exclude"]):
            continue
        if any(name.endswith(s) for s in cfg["files"]) and f.get("source") in ("original", "derivative"):
            wanted.append({"name": name, "size": int(f.get("size", 0)), "md5": f.get("md5"), "format": f.get("format")})
    return meta, wanted


def acquire(source_id: str, raw_dir: Path = RAW_DIR, manifest_dir: Path = MANIFEST_DIR) -> dict:
    conf = read_yaml(CONFIG_DIR / "acquire.yaml")
    cfg = {**conf["defaults"], **conf["sources"][source_id]}
    identifier = cfg["identifier"]
    _meta, files = plan(identifier, cfg)
    out = raw_dir / source_id
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"{source_id}.json"
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"files": {}}
    entries = {}
    for f in files:
        dest = out / f["name"]
        if dest.exists() and f["md5"] and md5_file(dest) == f["md5"]:
            LG.info("ok (cached) %s", f["name"])
        else:
            if dest.exists():  # upstream changed: keep the old file as a version, never overwrite
                stamp = dt.date.today().isoformat()
                dest.rename(dest.with_name(f"{dest.stem}.{stamp}{dest.suffix}"))
                LG.warning("upstream changed; kept old version of %s", f["name"])
            LG.info("download %s (%.1f MB)", f["name"], f["size"] / 1e6)
            http_get(f"{IA}/download/{identifier}/{f['name']}", dest, lg=LG)
            if f["md5"] and md5_file(dest) != f["md5"]:
                raise RuntimeError(f"MD5 mismatch for {f['name']}")
        prev = previous["files"].get(f["name"], {})
        entries[f["name"]] = {
            "bytes": dest.stat().st_size,
            "md5": f["md5"],
            "sha256": sha256_file(dest),
            "format": f["format"],
            "retrieved_on": prev.get("retrieved_on") or dt.date.today().isoformat(),
        }
    pages = page_count(out)
    manifest = {
        "source_id": source_id,
        "host": "internet-archive",
        "identifier": identifier,
        "url": f"{IA}/details/{identifier}",
        "iiif_manifest": f"https://iiif.archive.org/iiif/3/{identifier}/manifest.json",
        "scan_leaves": pages["leaves"],
        "printed_pages_mapped": pages["mapped"],
        "files": entries,
    }
    write_json(manifest_path, manifest)
    LG.info("manifest %s: %d files, %d leaves", manifest_path.name, len(entries), pages["leaves"])
    return manifest


def page_count(folder: Path) -> dict:
    """Exit check input: scan leaves from scandata vs. pages in the page-number map."""
    leaves = 0
    for p in folder.glob("*_scandata.xml"):
        leaves = p.read_text().count("<page ")
    mapped = 0
    for p in folder.glob("*_page_numbers.json"):
        mapped = len(json.loads(p.read_text()).get("pages", []))
    return {"leaves": leaves, "mapped": mapped}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--resume", action="store_true", help="accepted for CLI uniformity; acquire is always resumable")
    args = ap.parse_args(argv)
    m = acquire(args.source)
    if m["scan_leaves"] and m["printed_pages_mapped"] and m["scan_leaves"] != m["printed_pages_mapped"]:
        LG.warning("leaf count %d != page map %d — check before DP-01", m["scan_leaves"], m["printed_pages_mapped"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
