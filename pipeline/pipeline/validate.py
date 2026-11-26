"""Validate the source and media registers against JSON Schema (DP-15, TS-DATA-10, FR-MEDIA-07).

Usage: python -m pipeline.validate [--data-dir PATH]
Exit code 1 on any error, so CI blocks the build.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from pipeline import DATA_DIR, SCHEMA_DIR


def _registry() -> Registry:
    resources = []
    for p in SCHEMA_DIR.glob("*.schema.json"):
        doc = json.loads(p.read_text())
        res = Resource.from_contents(doc)
        resources += [(doc["$id"], res), (p.name, res)]
    return Registry().with_resources(resources)


def validator(schema_name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMA_DIR / schema_name).read_text())
    return Draft202012Validator(schema, registry=_registry())


def _duplicates(items: list[dict], key: str) -> list[str]:
    seen, dups = set(), []
    for it in items:
        k = it.get(key)
        if k in seen:
            dups.append(k)
        seen.add(k)
    return dups


def check_register(path: Path, schema_name: str, list_key: str, id_key: str) -> list[str]:
    if not path.exists():
        return [f"{path.name}: missing"]
    doc = yaml.safe_load(path.read_text()) or {}
    errors = [
        f"{path.name}: {'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
        for e in sorted(validator(schema_name).iter_errors(doc), key=lambda e: list(e.absolute_path))
    ]
    errors += [f"{path.name}: duplicate {id_key} '{d}'" for d in _duplicates(doc.get(list_key) or [], id_key)]
    return errors


def check_media_language(path: Path) -> list[str]:
    """FR-MEDIA-07/09: active media need alt text and caption in all three languages before production.
    Missing or/hi is reported as a warning until M7 (FR-LANG-05 fallback applies)."""
    doc = yaml.safe_load(path.read_text()) or {}
    warnings = []
    for m in doc.get("media") or []:
        if m.get("status") != "active":
            continue
        for field in ("alt_text", "caption"):
            for lang in ("or", "hi"):
                if not (m.get(field) or {}).get(lang):
                    warnings.append(f"{m.get('media_id')}: {field}.{lang} not yet translated")
    return warnings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = ap.parse_args(argv)
    d: Path = args.data_dir
    errors = check_register(d / "sources.yaml", "sources.schema.json", "sources", "source_id")
    errors += check_register(d / "media.yaml", "media.schema.json", "media", "media_id")
    warnings = check_media_language(d / "media.yaml") if (d / "media.yaml").exists() else []
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    print(f"validate: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
