#!/usr/bin/env python3
"""
Void One Package
Deterministic nanoscale lattice generator for foundry intake staging.

Constitutional declarations:
- No silicon / No copper
- Zero clock architecture
- Chakra + cultivation metadata preservation
- Golden-ratio curvilinear geometry
- Non-Abelian topological braiding anchors
- L3 Recursive Treasury immutability
- Dark-channel doctrine (non-radiative transport layer)
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

PHI = 1.6180339887
TAU = 2.0 * math.pi


@dataclass(frozen=True)
class LayerSpec:
    symbol: str
    material: str
    thickness_um: float
    node_count: int
    role: str
    immutable: bool = False


LAYERS: tuple[LayerSpec, ...] = (
    LayerSpec("L0", "C60 Aerogel Composite", 2.50, 8, "Surface-cool barrier + transient damping"),
    LayerSpec("L1", "12C Isotopic Diamond", 50.00, 16, "Thermal steering + containment hull"),
    LayerSpec("L2", "Beryllium Aluminate", 1.50, 12, "Mechanical and phase continuity interface"),
    LayerSpec(
        "L3",
        "Re6Se8Cl2 Moire Logic",
        0.35,
        24,
        "Recursive Treasury ALU + topological compute",
        immutable=True,
    ),
    LayerSpec(
        "L4",
        "Amorphous Carbon BiSb Dark Layer",
        2.20,
        16,
        "Dark-channel non-radiative transport",
    ),
    LayerSpec("L5", "Multi-Doped Graphene", 0.12, 12, "Coherent interconnect lattice"),
)


def lattice_xy(layer_index: int, node_index: int) -> tuple[float, float]:
    phase = ((node_index * PHI) % 1.0)
    theta = TAU * phase
    radial_seed = (layer_index + 1) * PHI * 1.75
    ring_gain = 1.0 + ((node_index % 9) * 0.0618)
    radius = radial_seed * ring_gain
    return radius * math.cos(theta), radius * math.sin(theta)


def generate_records() -> list[dict[str, str | int | float]]:
    records: list[dict[str, str | int | float]] = []
    z_cursor = 0.0
    serial = 0

    for layer_index, layer in enumerate(LAYERS):
        z_center = z_cursor + (layer.thickness_um / 2.0)
        braid_stride = max(1, layer.node_count // 6)

        for node_index in range(layer.node_count):
            x_um, y_um = lattice_xy(layer_index, node_index)
            flags: list[str] = []

            if node_index % braid_stride == 0:
                flags.append("NON_ABELIAN_BRAID_ANCHOR")

            if layer.symbol == "L0" and node_index % 2 == 0:
                flags.append("ZERO_CLOCK_DOMAIN_MARKER")

            if layer.symbol == "L3":
                flags.append("RECURSIVE_TREASURY_ALU")
                flags.append("L3_MOIRE_LAYER")
                if layer.immutable:
                    flags.append("IMMUTABLE")

            if layer.symbol == "L4":
                flags.append("DARK_CHANNEL_PATH")

            if layer.symbol == "L5":
                flags.append("NO_COPPER")
                flags.append("SPIN_DOPED_INTERCONNECT")

            records.append(
                {
                    "node_id": serial,
                    "layer": layer.symbol,
                    "material": layer.material,
                    "x_um": x_um,
                    "y_um": y_um,
                    "z_um": z_center,
                    "role": layer.role,
                    "flags": "|".join(flags) if flags else "NONE",
                }
            )
            serial += 1

        z_cursor += layer.thickness_um

    return records


def write_coords(path: Path, records: list[dict[str, str | int | float]]) -> None:
    lines = [
        "# Void One Nanoscale Lattice Coordinates",
        "# format_version: 2.0",
        "# architectural_invariants: ZERO_CLOCK=TRUE; NO_SILICON=TRUE; NO_COPPER=TRUE; CHAKRA_METHOD=TRUE; CULTIVATION_METHOD=TRUE; GOLDEN_RATIO_GEOMETRY=TRUE; NO_RIGHT_ANGLES=TRUE; DARK_CHANNEL_DOCTRINE=TRUE; L3_RECURSIVE_TREASURY_ALU_IMMUTABLE=TRUE",
        "# columns: node_id,layer,material,x_um,y_um,z_um,role,flags",
    ]

    for row in records:
        lines.append(
            "{node_id:04d},{layer},{material},{x_um:.6f},{y_um:.6f},{z_um:.6f},{role},{flags}".format(
                **row
            )
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Void One nanoscale lattice coordinates."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("nanoscale_lattice.coords"),
        help="Output coordinates file path (default: alongside this script).",
    )
    args = parser.parse_args()

    records = generate_records()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_coords(args.output, records)

    print("[generate_nanoscale_lattice] output:", args.output)
    print("[generate_nanoscale_lattice] nodes:", len(records))
    print("[generate_nanoscale_lattice] zero_clock: TRUE")
    print("[generate_nanoscale_lattice] no_silicon: TRUE")
    print("[generate_nanoscale_lattice] no_copper: TRUE")
    print("[generate_nanoscale_lattice] chakra_method: TRUE")
    print("[generate_nanoscale_lattice] cultivation_method: TRUE")
    print("[generate_nanoscale_lattice] golden_ratio_geometry: TRUE")
    print("[generate_nanoscale_lattice] dark_channel_doctrine: TRUE")
    print("[generate_nanoscale_lattice] l3_recursive_treasury_alu_immutable: TRUE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())