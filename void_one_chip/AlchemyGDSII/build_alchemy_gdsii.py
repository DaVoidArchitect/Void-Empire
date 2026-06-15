#!/usr/bin/env python3
"""
Build VOID Void One mask-map deliverables from nanoscale lattice coordinates.

Outputs:
- xenalchemy_core_mask_maps.gds
- xenalchemy_core_mask_maps.gdsii
- xenalchemy_core_mask_maps.gdsbin
- xenalchemy_core_mask_maps_geometry.json
- xenalchemy_core_mask_maps_coordinates.bin
"""

from __future__ import annotations

import json
import math
import struct
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import gdstk


PHI = 1.6180339887
GOLDEN_TURN_DEG = 137.507


def load_version_info(xen_root: Path) -> dict:
    path = xen_root / "VERSION.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}
    return payload if isinstance(payload, dict) else {}


@dataclass(frozen=True)
class CoordRecord:
    node_id: int
    layer: str
    material: str
    x_um: float
    y_um: float
    z_um: float
    role: str
    flags: str


def parse_coords(path: Path) -> list[CoordRecord]:
    records: list[CoordRecord] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue

        node_id, layer, material, x_um, y_um, z_um, role, flags = raw.split(",", 7)
        records.append(
            CoordRecord(
                node_id=int(node_id),
                layer=layer,
                material=material,
                x_um=float(x_um),
                y_um=float(y_um),
                z_um=float(z_um),
                role=role,
                flags=flags,
            )
        )
    return records


def build_gds(
    records: list[CoordRecord],
    out_gds: Path,
    version_info: dict,
) -> dict[str, tuple[int, int]]:
    lib = gdstk.Library(unit=1e-6, precision=1e-9)
    cell = lib.new_cell("XENALCHEMY_VOID_CORE")

    layer_map: dict[str, tuple[int, int]] = {
        "L0": (10, 0),
        "L1": (20, 0),
        "L2": (30, 0),
        "L3": (40, 0),
        "L4": (50, 0),
        "L5": (60, 0),
    }

    grouped: dict[str, list[CoordRecord]] = {}
    for rec in records:
        grouped.setdefault(rec.layer, []).append(rec)

    for layer, items in grouped.items():
        g_layer, g_dtype = layer_map[layer]
        items = sorted(items, key=lambda r: r.node_id)

        for idx, rec in enumerate(items):
            width = 0.115 + ((idx % 5) * 0.013)
            length = width * PHI
            angle = math.radians((idx * GOLDEN_TURN_DEG) % 360)

            poly = gdstk.ellipse(
                (rec.x_um, rec.y_um),
                radius=width,
                tolerance=0.001,
                layer=g_layer,
                datatype=g_dtype,
            )
            poly.scale(length / width, 1.0, center=(rec.x_um, rec.y_um))
            poly.rotate(angle, center=(rec.x_um, rec.y_um))
            cell.add(poly)

            marker = gdstk.ellipse(
                (rec.x_um, rec.y_um),
                radius=width * 0.34,
                tolerance=0.001,
                layer=g_layer,
                datatype=g_dtype,
            )
            cell.add(marker)

        for a, b in zip(items, items[1:] + items[:1]):
            ax, ay = a.x_um, a.y_um
            bx, by = b.x_um, b.y_um

            dx = bx - ax
            dy = by - ay
            seg = math.hypot(dx, dy) + 1e-12
            nx = -dy / seg
            ny = dx / seg

            mx = (ax + bx) * 0.5
            my = (ay + by) * 0.5
            bow = 0.17 + ((a.node_id % 7) * 0.011)
            cx = mx + (nx * bow)
            cy = my + (ny * bow)

            path = gdstk.FlexPath(
                [(ax, ay), (cx, cy), (bx, by)],
                width=0.026,
                joins="round",
                ends="round",
                bend_radius=0.07,
                layer=g_layer,
                datatype=g_dtype,
                tolerance=0.001,
            )
            cell.add(*path.to_polygons())

    meta = lib.new_cell("XENALCHEMY_VOID_META")
    lines = [
        "ZERO_CLOCK=TRUE",
        "NO_SILICON=TRUE",
        "NO_COPPER=TRUE",
        "CHAKRA_METHOD=TRUE",
        "CULTIVATION_METHOD=TRUE",
        "NO_90_DEGREE_TURNS=TRUE",
        "NO_ORTHOGONAL_GRID_ROUTING=TRUE",
        "DARK_CHANNEL_DOCTRINE=TRUE",
        "GOLDEN_RATIO_GEOMETRY=TRUE",
    ]
    design_version = str(version_info.get("design_version", "UNKNOWN"))
    release_id = str(version_info.get("release_id", "UNKNOWN"))
    program_id = str(version_info.get("program_id", "UNKNOWN"))
    lines.extend(
        [
            f"DESIGN_VERSION={design_version}",
            f"RELEASE_ID={release_id}",
            f"PROGRAM_ID={program_id}",
        ]
    )
    y = 0.0
    for line in lines:
        meta.add(*gdstk.text(line, 0.55, (0, y), layer=199, datatype=0))
        y -= 0.85
    cell.add(gdstk.Reference(meta, origin=(35.0, -35.0)))

    lib.write_gds(out_gds)
    return layer_map


def write_geometry_json(
    out_path: Path,
    source_coords: Path,
    gds_path: Path,
    layer_map: dict[str, tuple[int, int]],
    records: list[CoordRecord],
    version_info: dict,
) -> None:
    payload = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "source_coords": source_coords.as_posix(),
        "gds_path": gds_path.as_posix(),
        "design_version": str(version_info.get("design_version", "UNKNOWN")),
        "release_id": str(version_info.get("release_id", "UNKNOWN")),
        "program_id": str(version_info.get("program_id", "UNKNOWN")),
        "certification_target": str(version_info.get("certification_target", "UNKNOWN")),
        "constraints": {
            "zero_clock": True,
            "no_silicon": True,
            "no_copper": True,
            "chakra_method": True,
            "cultivation_method": True,
            "dark_channel_doctrine": True,
            "golden_ratio_geometry": True,
            "no_90_degree_turns": True,
            "no_orthogonal_grid_routing": True,
        },
        "golden_ratio": PHI,
        "preferred_turn_deg": GOLDEN_TURN_DEG,
        "layer_map": {k: {"layer": v[0], "datatype": v[1]} for k, v in layer_map.items()},
        "record_count": len(records),
        "records": [
            {
                "node_id": r.node_id,
                "layer": r.layer,
                "material": r.material,
                "x_um": r.x_um,
                "y_um": r.y_um,
                "z_um": r.z_um,
                "role": r.role,
                "flags": r.flags,
            }
            for r in records
        ],
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_binary_coordinate_map(out_path: Path, records: list[CoordRecord]) -> None:
    with out_path.open("wb") as f:
        f.write(b"XMAP")
        f.write(struct.pack("<H", 2))
        f.write(struct.pack("<I", len(records)))

        for r in records:
            layer_index = int(r.layer[1:])
            f.write(struct.pack("<I", r.node_id))
            f.write(struct.pack("<B", layer_index))
            f.write(struct.pack("<ddd", r.x_um, r.y_um, r.z_um))


def main() -> int:
    out_dir = Path(__file__).resolve().parent
    xen_root = out_dir.parent
    coords_path = xen_root / "VOID_Sovereign_Core_Package" / "nanoscale_lattice.coords"
    version_info = load_version_info(xen_root)

    records = parse_coords(coords_path)

    gds_path = out_dir / "xenalchemy_core_mask_maps.gds"
    gdsii_path = out_dir / "xenalchemy_core_mask_maps.gdsii"
    gdsbin_path = out_dir / "xenalchemy_core_mask_maps.gdsbin"
    geom_path = out_dir / "xenalchemy_core_mask_maps_geometry.json"
    coord_bin_path = out_dir / "xenalchemy_core_mask_maps_coordinates.bin"

    layer_map = build_gds(records, gds_path, version_info)

    gds_blob = gds_path.read_bytes()
    gdsii_path.write_bytes(gds_blob)
    gdsbin_path.write_bytes(gds_blob)

    write_geometry_json(geom_path, coords_path, gds_path, layer_map, records, version_info)
    write_binary_coordinate_map(coord_bin_path, records)

    print(f"generated: {gds_path}")
    print(f"generated: {gdsii_path}")
    print(f"generated: {gdsbin_path}")
    print(f"generated: {geom_path}")
    print(f"generated: {coord_bin_path}")
    print(f"records: {len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())