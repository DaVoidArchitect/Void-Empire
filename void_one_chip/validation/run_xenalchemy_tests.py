#!/usr/bin/env python3
"""
Master Void One validation runner.

Executes:
- SymbiYosys formal checks
- TCAD thermal gradient + transmutation band checks
- Dark-channel mesh checks
- Material hard-law compliance checks
- Optional synthetic PDK viability gate (enabled via env)

Prints final "TAPE-OUT READY" verdict when all checks pass.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    return payload if isinstance(payload, dict) else {}


def read_version_info() -> dict[str, str]:
    payload = read_json(ROOT.parent / "VERSION.json")
    return {
        "design_version": str(payload.get("design_version", "UNKNOWN")),
        "release_id": str(payload.get("release_id", "UNKNOWN")),
        "program_id": str(payload.get("program_id", "UNKNOWN")),
    }


def env_flag(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def run_cmd(
    cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None
) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout


def _prepend_path(env: dict[str, str], p: Path) -> None:
    if not p.exists():
        return
    old_path = env.get("PATH", "")
    parts = old_path.split(os.pathsep) if old_path else []
    p_str = str(p)
    if p_str not in parts:
        env["PATH"] = p_str + (os.pathsep + old_path if old_path else "")


def build_formal_env() -> dict[str, str]:
    env = os.environ.copy()

    # Ensure Python Scripts/bin dir is available for YoWASP wrappers.
    py_dir = Path(sys.executable).resolve().parent
    _prepend_path(env, py_dir)
    if py_dir.name == "Scripts":
        # Check parent bin as well (where z3 is on Windows)
        _prepend_path(env, py_dir.parent / "bin")
    else:
        scripts_dir = py_dir / "Scripts"
        _prepend_path(env, scripts_dir)

    # Optional explicit solver path override.
    z3_bin_override = env.get("XENALCHEMY_Z3_BIN", "").strip()
    if z3_bin_override:
        _prepend_path(env, Path(z3_bin_override))
    else:
        # Default local tooling location used in this repository.
        default_z3_bin = (
            ROOT.parent.parent
            / "_tooling"
            / "z3-4.16.0-x64-win"
            / "z3-4.16.0-x64-win"
            / "bin"
        )
        _prepend_path(env, default_z3_bin)

    return env


def resolve_in_path(cmd_names: list[str], env: dict[str, str]) -> str | None:
    path_value = env.get("PATH", "")
    for name in cmd_names:
        resolved = shutil.which(name, path=path_value)
        if resolved is not None:
            return resolved
    return None


def run_formal() -> dict:
    require_formal = env_flag("XENALCHEMY_REQUIRE_SBY", "0")

    env = build_formal_env()
    sby_exe = resolve_in_path(["sby", "yowasp-sby", "yowasp-sby.exe"], env)

    if sby_exe is None:
        note = "sby/yowasp-sby not found in PATH"
        if require_formal:
            return {
                "pass": False,
                "skipped": True,
                "note": f"{note}; strict gate enforced by XENALCHEMY_REQUIRE_SBY=1",
            }
        return {
            "pass": True,
            "skipped": True,
            "note": f"{note}; formal gate skipped (set XENALCHEMY_REQUIRE_SBY=1 to enforce)",
        }

    cmd = [sby_exe]
    sby_name = Path(sby_exe).name.lower()
    if sby_name.startswith("yowasp-sby"):
        cmd.extend(
            [
                "--yosys",
                "yowasp-yosys.exe",
                "--smtbmc",
                "yowasp-yosys-smtbmc.exe",
                "--witness",
                "yowasp-yosys-witness.exe",
            ]
        )
    cmd.extend(["-f", "formal_core.sby"])

    rc, out = run_cmd(cmd, cwd=ROOT, env=env)
    return {
        "pass": rc == 0,
        "rc": rc,
        "log": out[-4000:],
        "skipped": False,
        "tool": Path(sby_exe).name,
    }


def run_python_script(script_name: str) -> dict:
    rc, out = run_cmd([sys.executable, script_name], cwd=ROOT)
    return {"pass": rc == 0, "rc": rc, "log": out[-4000:]}


def run_synthetic_pdk_gate() -> dict:
    enabled = env_flag("XENALCHEMY_ENABLE_SPDK", "0")
    if not enabled:
        return {
            "pass": True,
            "skipped": True,
            "note": "synthetic PDK gate disabled (set XENALCHEMY_ENABLE_SPDK=1 to enforce)",
        }

    repo_root = ROOT.parent
    auto_generate = env_flag("XENALCHEMY_SPDK_AUTOGEN", "1")
    logs: list[str] = []

    if auto_generate:
        generator = repo_root / "tools" / "generate_synthetic_pdk.py"
        if not generator.exists():
            return {
                "pass": False,
                "skipped": False,
                "note": f"synthetic PDK generator missing: {generator}",
            }

        rc_gen, out_gen = run_cmd([sys.executable, str(generator)], cwd=repo_root)
        logs.append(out_gen)
        if rc_gen != 0:
            return {
                "pass": False,
                "rc": rc_gen,
                "log": "\n".join(logs)[-4000:],
                "skipped": False,
                "stage": "generate_synthetic_pdk",
            }

    rc_gate, out_gate = run_cmd([sys.executable, "synthetic_pdk_gate.py"], cwd=ROOT)
    logs.append(out_gate)

    return {
        "pass": rc_gate == 0,
        "rc": rc_gate,
        "log": "\n".join(logs)[-4000:],
        "skipped": False,
        "autogen": auto_generate,
    }


def main() -> int:
    version_info = read_version_info()

    ordered_sections = [
        "clockless",
        "formal",
        "tcad",
        "defect_connectome",
        "void_channel",
        "material_compliance",
        "yield_model",
    ]

    summary = {
        "clockless": run_python_script("clockless_gate.py"),
        "formal": run_formal(),
        "tcad": run_python_script("tcad_isotopic_diamond.py"),
        "defect_connectome": run_python_script("defect_connectome_mesh.py"),
        "void_channel": run_python_script("void_channel_mesh.py"),
        "material_compliance": run_python_script("material_compliance_check.py"),
    }

    # Write intermediate report to disk so tools/generate_yield_report.py can read fresh formal results
    summary["overall_pass"] = False
    summary["version"] = version_info
    out_path = ROOT / "xenalchemy_test_report.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Run yield model and gate
    summary["yield_model"] = run_python_script("../tools/generate_yield_report.py")
    summary["yield_gate"] = run_python_script("yield_gate.py")
    ordered_sections.append("yield_gate")

    if env_flag("XENALCHEMY_ENABLE_SPDK", "0"):
        summary["synthetic_pdk"] = run_synthetic_pdk_gate()
        ordered_sections.append("synthetic_pdk")

    overall = all(summary[name].get("pass", False) for name in ordered_sections)
    summary["overall_pass"] = overall
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("=== Void One Validation Summary ===")
    print(
        "version:",
        version_info["design_version"],
        "release:",
        version_info["release_id"],
    )
    for k in ordered_sections:
        status = "PASS" if summary[k]["pass"] else "FAIL"
        if summary[k].get("skipped", False):
            status += " (SKIPPED)"
        print(f"{k}: {status}")

    if overall:
        print("\nTAPE-OUT READY")
        return 0

    print("\nNOT READY")
    print(f"Detailed report: {out_path}")
    return 5


if __name__ == "__main__":
    raise SystemExit(main())
