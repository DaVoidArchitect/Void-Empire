from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TelemetrySnapshot:
    thermal_input_milliK: int
    defect_density: int
    collapse_guard: bool


class TelemetryAdapter:
    """Deterministic telemetry adapter for scheduler/service policy surfaces."""

    def capture(
        self,
        *,
        thermal_input_milliK: int,
        defect_density: int,
        collapse_guard: bool,
    ) -> TelemetrySnapshot:
        thermal_input_milliK = max(0, int(thermal_input_milliK))
        defect_density = max(0, min(255, int(defect_density)))
        return TelemetrySnapshot(
            thermal_input_milliK=thermal_input_milliK,
            defect_density=defect_density,
            collapse_guard=bool(collapse_guard),
        )
