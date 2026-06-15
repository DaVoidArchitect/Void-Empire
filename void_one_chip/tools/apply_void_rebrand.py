#!/usr/bin/env python3
"""Apply VOID, Inc. / Void One branding across the VoidAlchmey workspace.

This script performs textual replacements only (no file renames) so existing
tooling and test entrypoints remain executable.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TEXT_EXTS = {
    ".md",
    ".txt",
    ".tex",
    ".json",
    ".py",
    ".sv",
    ".sby",
    ".html",
    ".yaml",
    ".yml",
    ".coords",
    ".csv",
}


REPLACEMENTS = [
    # Absolute and relative paths.
    (
        "C:/Users/dacoo/Desktop/Artifact_Origins/Xenalchemy/",
        "C:/Users/dacoo/Desktop/Artifact_Origins/VoidAlchmey/",
    ),
    (
        "C:\\Users\\dacoo\\Desktop\\Artifact_Origins\\Xenalchemy\\",
        "C:\\Users\\dacoo\\Desktop\\Artifact_Origins\\VoidAlchmey\\",
    ),
    ("Artifact_Origins/Xenalchemy/", "Artifact_Origins/VoidAlchmey/"),
    ("Artifact_Origins\\Xenalchemy\\", "Artifact_Origins\\VoidAlchmey\\"),
    ("python Xenalchemy/", "python VoidAlchmey/"),
    ("`Xenalchemy/", "`VoidAlchmey/"),
    ("Xenalchemy/", "VoidAlchmey/"),
    # Business / product branding.
    ("VOID Void One", "Void One"),
    ("Xenalchemy Sovereign Void Core", "VOID Void One"),
    ("SOVEREIGN VOID CORE", "VOID ONE"),
    ("SOVEREIGN VOID", "VOID ONE"),
    ("Sovereign Void", "Void One"),
    ("Sovereign Void Cores", "Void One systems"),
    ("Sovereign Void Core", "Void One"),
    ("Soverign Void Core", "Void One"),
    ("Xenalchemy Systems", "VOID, Inc."),
    ("Xenalchemy |", "VOID |"),
    ("Xenalchemy", "VOID"),
    # Program / release identifiers.
    ("XSVC-FMP-ALE-950K-V2.0-FRONTIER-R1", "VOID-FMP-ALE-950K-V2.0-FRONTIER-R1"),
    ("XSVC-VOID-2.0-FRONTIER-R1", "VOIDONE-2.0-FRONTIER-R1"),
    ("XSVC-MASTER-TAPEOUT-VOID-2.0", "VOID-MASTER-TAPEOUT-ONE-2.0"),
    ("XEN-VOID-GDSII-PFLOW-V2.0-FRONTIER-R1", "VOIDONE-GDSII-PFLOW-V2.0-FRONTIER-R1"),
]


def apply_rebrand() -> tuple[int, list[str]]:
    changed: list[str] = []
    self_path = Path(__file__).resolve()

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.resolve() == self_path:
            continue
        if path.suffix.lower() not in TEXT_EXTS:
            continue

        try:
            original = path.read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            continue

        updated = original
        for src, dst in REPLACEMENTS:
            updated = updated.replace(src, dst)

        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed.append(path.relative_to(ROOT).as_posix())

    return len(changed), changed


def main() -> int:
    count, changed = apply_rebrand()
    print(f"[void_rebrand] changed_files={count}")
    for rel in changed[:200]:
        print(rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
