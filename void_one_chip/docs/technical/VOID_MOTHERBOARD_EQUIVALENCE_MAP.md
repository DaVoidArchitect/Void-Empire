# VOID Motherboard-Equivalence Architecture Map (Pulse/Governance Aligned)

## Purpose
Map conventional motherboard chip functions into the VOID pulse-driven,
capability-gated, audit-coupled architecture without violating constitutional
constraints.

---

## 1) Conventional Board Function → VOID Module Mapping

| Conventional Function Class | VOID Layer | VOID Module(s) | Governed Domain | Capability Rights |
|---|---|---|---|---|
| Boot ROM / early init | HAL + Kernel | `hal/memory_fabric.py`, `kernel/boot_power_governor.py` | `power`, `memory` | `POWER_TRANSITION`, `MEMORY_READ` |
| DRAM controller / memory fabric | HAL + Services | `hal/memory_fabric.py`, `services/platform_service.py` | `memory` | `MEMORY_WRITE`, `MEMORY_READ` |
| Storage controller | HAL + Services | `hal/storage_bridge.py`, `services/platform_service.py` | `storage` | `STORAGE_WRITE`, `STORAGE_READ` |
| Southbridge I/O routing | HAL + Kernel + Services | `hal/io_bus.py`, `kernel/event_router.py`, `services/platform_service.py` | `io`, `platform` | `IO_EMIT`, `IO_POLL`, `ROUTE_EVENT` |
| NIC / packet I/O | HAL + Services | `hal/network_link.py`, `services/platform_service.py` | `network` | `NETWORK_TX`, `NETWORK_RX` |
| Peripheral control (sensor/actuator buses) | HAL + Services | `hal/peripheral_plane.py`, `services/platform_service.py` | `peripheral` | `PERIPHERAL_COMMAND`, `PERIPHERAL_QUERY` |
| Device enumeration / registry | Kernel + Services | `kernel/device_registry.py`, `services/platform_service.py` | `device` | `DEVICE_REGISTER`, `DEVICE_REMOVE` |
| Platform policy gateway | API | `apis/intent_adapter.py`, `apis/gateway.py` | all | signed intents + per-domain rights |

### 1b) Complete Single-Chip Merge Coverage Matrix

This matrix extends baseline board mapping into a **single-chip merged control model**
for motherboard-class function coverage at repo/runtime level.

| Motherboard Class | VOID Realization | Domain(s) | Rights |
|---|---|---|---|
| CPU package orchestration | `services/platform_service.py` + scheduler | `platform`, `power` | `ROUTE_EVENT`, `POWER_TRANSITION` |
| DRAM controller | `hal/memory_fabric.py` | `memory` | `MEMORY_WRITE`, `MEMORY_READ` |
| NVMe/SATA controller | `hal/storage_bridge.py` | `storage` | `STORAGE_WRITE`, `STORAGE_READ` |
| PCIe / southbridge fabric | `hal/io_bus.py` + `kernel/event_router.py` | `io`, `platform` | `IO_EMIT`, `IO_POLL`, `ROUTE_EVENT` |
| NIC / link I/O | `hal/network_link.py` | `network` | `NETWORK_TX`, `NETWORK_RX` |
| Peripheral buses (I2C/SPI/GPIO-class) | `hal/peripheral_plane.py` | `peripheral` | `PERIPHERAL_COMMAND`, `PERIPHERAL_QUERY` |
| Device enumeration / inventory | `kernel/device_registry.py` | `device` | `DEVICE_REGISTER`, `DEVICE_REMOVE` |
| Boot and power sequencing | `kernel/boot_power_governor.py` | `power` | `POWER_TRANSITION` |
| Deterministic interrupt/event routing | `kernel/event_router.py` + scheduler ordering | `platform` | `ROUTE_EVENT` |
| Mailbox/control plane ingress | `hal/mailbox.py` + signed intent adapter | all | signed intent + nonce/counter replay guards |
| Timer/counter source | `hal/counter.py` | all | monotonic per `(domain,subnet)` |
| Trusted audit chain | `kernel/event_journal.py` | all governed | audit append required before commit |
| Economy rails (payments/tariffs) | `services/treasury_service.py` | `treasury` | `TREASURY_TRANSFER` |
| Work contract economy | `services/quest_service.py` | `quest` | `QUEST_CLAIM`, `QUEST_SUBMIT_PROOF`, `QUEST_SETTLE` |
| Provenance legacy ledger | `services/legacy_service.py` | `legacy` | `LEGACY_APPEND` |
| Knowledge/IP control plane | `services/knowledge_service.py` | `knowledge` | `KNOWLEDGE_REGISTER`, `KNOWLEDGE_GRANT` |
| Constitutional civic governance | `services/governance_service.py` | `governance` | `GOVERNANCE_VOTE`, `GOVERNANCE_FINALIZE` |

Coverage is asserted by:
- `validation/platform_board_conformance_report.json`
- `validation/motherboard_equivalence_report.json`

---

## 2) Invariants (Must Hold)

1. **No direct mutation path** bypasses capability checks and event journal append.
2. **All privileged board operations** are represented as signed intents and routed
   through governed dispatch.
3. **Deterministic ordering** is preserved via domain priorities + monotonic counters.
4. **Replay resistance** is preserved at intent and event-journal layers.
5. **Boot/power state changes** are legal-transition constrained and auditable.

---

## 3) Conformance Evidence Targets

- `validation/platform_board_conformance_report.json`
  - device registration / removal semantics
  - boot-power legal/illegal transition checks
  - memory read/write governance and replay-safe journaling
  - storage block governance
  - I/O endpoint emit/poll governance
  - network tx/rx governance + duplicate packet prevention
  - peripheral command/query governance
  - routed event dispatch determinism

- `validation/motherboard_equivalence_report.json`
  - complete board-class mapping completeness check
  - domain and right coverage completeness check
  - gateway route smoke for motherboard domains

---

## 4) Realism Boundary

This map establishes **repo-level motherboard-equivalent control semantics**.
It does not, by itself, replace external PHY/electrical compliance,
manufacturing qualification, or deployment certifications.
