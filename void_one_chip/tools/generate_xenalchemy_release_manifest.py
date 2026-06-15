#!/usr/bin/env python3
"""Generate a full-file release manifest for VOID.

This binds documents, source, validation outputs, and GDSII artifacts to
a single version/release checksum snapshot.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VERSION_PATH = ROOT / "VERSION.json"
OUT_PATH = ROOT / "validation" / "xenalchemy_release_manifest.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    return payload if isinstance(payload, dict) else {}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def category_for(path: Path) -> str:
    rel = path.relative_to(ROOT)
    top = rel.parts[0] if rel.parts else "root"
    if top in {
        "src",
        "validation",
        "tools",
        "pdk",
        "docs",
        "AlchemyGDSII",
        "VOID_Sovereign_Core_Package",
    }:
        return top
    if rel.suffix.lower() in {".md", ".txt", ".tex", ".html", ".json", ".yaml", ".yml"}:
        return "documentation_or_metadata"
    return "misc"


def iter_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if rel.parts and rel.parts[0] == ".git":
            continue
        # Exclude output file itself to avoid self-hash recursion.
        if path.resolve() == OUT_PATH.resolve():
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix())


def file_record(path: Path) -> dict[str, Any]:
    rel = path.relative_to(ROOT).as_posix()
    stat = path.stat()
    return {
        "path": rel,
        "category": category_for(path),
        "size_bytes": int(stat.st_size),
        "sha256": sha256_file(path),
    }


def main() -> int:
    version = read_json(VERSION_PATH)
    if not version:
        raise SystemExit(f"missing or invalid version file: {VERSION_PATH}")

    records = [file_record(p) for p in iter_files()]
    aggregate = hashlib.sha256()
    for rec in records:
        aggregate.update(rec["path"].encode("utf-8"))
        aggregate.update(rec["sha256"].encode("utf-8"))

    payload = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "design_name": str(version.get("design_name", "Void One")),
        "design_version": str(version.get("design_version", "UNKNOWN")),
        "release_id": str(version.get("release_id", "UNKNOWN")),
        "program_id": str(version.get("program_id", "UNKNOWN")),
        "certification_target": str(version.get("certification_target", "UNKNOWN")),
        "file_count": len(records),
        "tree_sha256": aggregate.hexdigest(),
        "files": records,
    }

    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("[release_manifest] design_version:", payload["design_version"])
    print("[release_manifest] release_id:", payload["release_id"])
    print("[release_manifest] file_count:", payload["file_count"])
    print("[release_manifest] tree_sha256:", payload["tree_sha256"])
    print("[release_manifest] output:", OUT_PATH)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
