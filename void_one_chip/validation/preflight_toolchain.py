#!/usr/bin/env python3
"""
Preflight validator for Void strict release gates.

This script verifies that the local environment has the required Python runtime,
packages, and formal toolchain binaries before running strict validation gates.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import platform
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VALIDATION_DIR = ROOT / "validation"
REQ_PATH = VALIDATION_DIR / "requirements.txt"
REPORT_PATH = VALIDATION_DIR / "preflight_toolchain_report.json"

DEFAULT_Z3_BIN_DIR = (
    ROOT.parent
    / "_tooling"
    / "z3-4.16.0-x64-win"
    / "z3-4.16.0-x64-win"
    / "bin"
)

IMPORT_NAME_OVERRIDES = {
    "z3-solver": "z3",
    "pyyaml": "yaml",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Void strict toolchain prerequisites.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict checks (same posture used by strict release gating).",
    )
    return parser.parse_args()


def env_flag(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def parse_requirements(path: Path) -> list[str]:
    if not path.exists():
        return []

    packages: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        item = line.strip()
        if not item or item.startswith("#"):
            continue
        item = item.split("==", 1)[0].split(">=", 1)[0].split("<=", 1)[0].strip()
        if item:
            packages.append(item)
    return packages


def package_required(package: str, strict: bool) -> bool:
    pkg = package.lower()

    # devsim is optional by default because tcad currently supports
    # an analytic fallback model when full native math backends are unavailable.
    if pkg == "devsim":
        return env_flag("XENALCHEMY_REQUIRE_DEVSIM", "0")

    return strict


def check_python_runtime() -> dict[str, Any]:
    min_major, min_minor = 3, 10
    v = sys.version_info
    ok = (v.major, v.minor) >= (min_major, min_minor)
    return {
        "pass": ok,
        "version": platform.python_version(),
        "executable": sys.executable,
        "required_min": f"{min_major}.{min_minor}",
    }


def check_python_packages(requirements: list[str], strict: bool) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for pkg in requirements:
        import_name = IMPORT_NAME_OVERRIDES.get(pkg.lower(), pkg.replace("-", "_"))
        required = package_required(pkg, strict=strict)

        # Use non-import probing for devsim to avoid forcing native DLL load
        # when runtime is configured to permit analytic fallback.
        if pkg.lower() == "devsim" and not required:
            spec = importlib.util.find_spec(import_name)
            results.append(
                {
                    "package": pkg,
                    "import_name": import_name,
                    "required": required,
                    "pass": spec is not None,
                    "detail": "module spec found (optional runtime dependency)"
                    if spec is not None
                    else "module spec missing (optional runtime dependency)",
                }
            )
            continue

        try:
            importlib.import_module(import_name)
            results.append(
                {
                    "package": pkg,
                    "import_name": import_name,
                    "required": required,
                    "pass": True,
                    "detail": "import ok",
                }
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                {
                    "package": pkg,
                    "import_name": import_name,
                    "required": required,
                    "pass": False,
                    "detail": f"import failed: {exc}",
                }
            )
    return results


def resolve_executable_from_dir(directory: Path, base_name: str) -> str | None:
    candidates = [base_name]
    if os.name == "nt":
        candidates.extend([f"{base_name}.exe", f"{base_name}.cmd", f"{base_name}.bat"])

    for name in candidates:
        p = directory / name
        if p.exists() and p.is_file():
            return str(p)
    return None


def resolve_any_executable(names: list[str], extra_dirs: list[Path] | None = None) -> str | None:
    for n in names:
        path = shutil.which(n)
        if path:
            return path

    if not extra_dirs:
        return None

    for d in extra_dirs:
        if not d.exists() or not d.is_dir():
            continue
        for n in names:
            resolved = resolve_executable_from_dir(d, n)
            if resolved:
                return resolved

    return None


def resolve_z3() -> tuple[bool, str | None, str]:
    override = os.environ.get("XENALCHEMY_Z3_BIN", "").strip()

    if override:
        p = Path(override)
        if p.is_file():
            return (True, str(p), "resolved from XENALCHEMY_Z3_BIN file")
        if p.is_dir():
            resolved = resolve_executable_from_dir(p, "z3")
            if resolved:
                return (True, resolved, "resolved from XENALCHEMY_Z3_BIN directory")
            return (False, None, "XENALCHEMY_Z3_BIN directory does not contain z3 executable")
        return (False, None, "XENALCHEMY_Z3_BIN path does not exist")

    path_hit = shutil.which("z3")
    if path_hit:
        return (True, path_hit, "resolved from PATH")

    # Add virtual environment bin directory to check on Windows
    py_dir = Path(sys.executable).resolve().parent
    if py_dir.name == "Scripts":
        venv_bin = py_dir.parent / "bin"
        resolved = resolve_executable_from_dir(venv_bin, "z3")
        if resolved:
            return (True, resolved, "resolved from venv bin directory")

    fallback = resolve_executable_from_dir(DEFAULT_Z3_BIN_DIR, "z3")
    if fallback:
        return (True, fallback, "resolved from default fallback tooling directory")

    return (False, None, "z3 not found in PATH, XENALCHEMY_Z3_BIN, or fallback tooling path")


def check_binaries(strict: bool) -> dict[str, dict[str, Any]]:
    py_dir = Path(sys.executable).resolve().parent
    extra_dirs = [py_dir]
    if py_dir.name == "Scripts":
        venv_bin = py_dir.parent / "bin"
        if venv_bin.exists():
            extra_dirs.append(venv_bin)
    else:
        scripts_dir = py_dir / "Scripts"
        if scripts_dir.exists():
            extra_dirs.append(scripts_dir)

    sby_path = resolve_any_executable(["sby", "yowasp-sby"], extra_dirs)
    yosys_path = resolve_any_executable(["yosys", "yowasp-yosys"], extra_dirs)
    smtbmc_path = resolve_any_executable(["yosys-smtbmc", "yowasp-yosys-smtbmc"], extra_dirs)
    z3_ok, z3_path, z3_detail = resolve_z3()

    checks: dict[str, dict[str, Any]] = {
        "sby": {
            "pass": bool(sby_path),
            "path": sby_path,
            "detail": "requires sby/yowasp-sby",
        },
        "yosys": {
            "pass": bool(yosys_path),
            "path": yosys_path,
            "detail": "requires yosys/yowasp-yosys",
        },
        "yosys_smtbmc": {
            "pass": bool(smtbmc_path),
            "path": smtbmc_path,
            "detail": "requires yosys-smtbmc/yowasp-yosys-smtbmc",
        },
        "z3": {
            "pass": z3_ok,
            "path": z3_path,
            "detail": z3_detail,
        },
    }

    # In strict mode, all formal stack binaries are mandatory.
    if not strict:
        # Non-strict keeps results informational but still reports current status.
        for item in checks.values():
            item["required"] = False
    else:
        for item in checks.values():
            item["required"] = True

    return checks


def main() -> int:
    args = parse_args()
    strict = bool(args.strict or env_flag("XENALCHEMY_PREFLIGHT_STRICT", "0"))

    requirements = parse_requirements(REQ_PATH)
    python_check = check_python_runtime()
    package_checks = check_python_packages(requirements, strict=strict)
    binary_checks = check_binaries(strict=strict)

    required_packages = [item for item in package_checks if item.get("required", False)]
    package_pass = all(item.get("pass", False) for item in required_packages)
    binary_pass = all(item.get("pass", False) for item in binary_checks.values())

    payload = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "strict_mode": strict,
        "python": python_check,
        "requirements_path": str(REQ_PATH),
        "package_checks": package_checks,
        "binary_checks": binary_checks,
        "pass": bool(python_check.get("pass", False) and package_pass and binary_pass),
    }

    REPORT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("[preflight] strict_mode:", strict)
    print("[preflight] python_pass:", python_check.get("pass", False))
    print("[preflight] required_package_count:", len(required_packages))
    print("[preflight] package_pass:", package_pass)
    print("[preflight] binary_pass:", binary_pass)
    print("[preflight] pass:", payload["pass"])
    print("[preflight] report:", REPORT_PATH)

    return 0 if payload["pass"] else 11


if __name__ == "__main__":
    raise SystemExit(main())
