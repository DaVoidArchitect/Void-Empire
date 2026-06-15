#!/usr/bin/env python3
"""
Material hard-law compliance gate for Void One.

Hard-fails if silicon or copper usage is detected in the Golden BOM.
Explicit prohibition notes (for example "no silicon" / "copper prohibited")
are treated as compliant policy constraints, not violations.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path


FORBIDDEN_TERMS = ("silicon", "si", "copper", "cu")
NEGATION_PATTERNS = (
    r"\bno\s+{term}\b",
    r"\bwithout\s+{term}\b",
    r"\b{term}\s+prohibited\b",
    r"\bprohibit(?:ed|s|ion)?\s+{term}\b",
    r"\b{term}\s+forbidden\b",
    r"\bforbidden\s+{term}\b",
    r"\bban(?:ned|s)?\s+{term}\b",
    r"\b{term}\s+free\b",
)


def normalize(text: str) -> str:
    return text.lower().replace("-", " ").replace("_", " ")


def term_present(text: str, term: str) -> bool:
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def is_negated_reference(text: str, term: str) -> bool:
    for pattern in NEGATION_PATTERNS:
        if re.search(pattern.format(term=re.escape(term)), text):
            return True
    return False


def find_violating_terms(text: str) -> list[str]:
    t = normalize(text)
    violations: list[str] = []
    for term in FORBIDDEN_TERMS:
        if term_present(t, term) and not is_negated_reference(t, term):
            violations.append(term)
    return sorted(set(violations))


def contains_forbidden(text: str) -> bool:
    return len(find_violating_terms(text)) > 0


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    bom_path = root / "pdk" / "XENALCHEMY_Golden_BOM.csv"

    violations: list[dict[str, str]] = []
    with bom_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_text = " ".join(str(v) for v in row.values() if v is not None)
            violating_terms = find_violating_terms(row_text)
            if violating_terms:
                violations.append(
                    {
                        "item_id": str(row.get("item_id", "")),
                        "material": str(row.get("material", "")),
                        "composition": str(row.get("composition", "")),
                        "notes": str(row.get("notes", "")),
                        "violating_terms": violating_terms,
                    }
                )

    payload = {
        "bom_path": str(bom_path),
        "forbidden_terms": FORBIDDEN_TERMS,
        "violations": violations,
        "pass": len(violations) == 0,
    }

    out_path = Path(__file__).resolve().parent / "material_compliance_report.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("[material_compliance] pass:", payload["pass"])
    print("[material_compliance] violations:", len(violations))

    return 0 if payload["pass"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
