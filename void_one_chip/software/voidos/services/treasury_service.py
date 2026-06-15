from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from ..kernel.capabilities import Capability
from ..kernel.mutation_coordinator import MutationCoordinator


INTER_SUBNET_TARIFF_BPS = 618
INTRA_SUBNET_LEASE_BPS = 16
BPS_DENOM = 10_000


@dataclass(frozen=True)
class TreasuryResult:
    inter_subnet: bool
    tariff_value: int
    lease_value: int
    routed_value: int
    treasury_credit: int


@dataclass(frozen=True)
class TreasuryGovernedResult:
    ok: bool
    code: str
    committed: bool
    event_id: str
    settlement: TreasuryResult
    detail: str = ""


class TreasurySettlementService:
    """Policy-level mirror of Void hard-law treasury routing semantics."""

    def __init__(self, *, coordinator: MutationCoordinator | None = None) -> None:
        self._coordinator = coordinator or MutationCoordinator()

    @property
    def committed_state(self) -> dict[str, dict[str, object]]:
        return self._coordinator.committed_state

    def snapshot(self) -> dict[str, Any]:
        return {
            "coordinator": self._coordinator.snapshot(),
        }

    def settle(self, *, src_subnet_id: int, dst_subnet_id: int, tx_value: int, collapse_guard: bool) -> TreasuryResult:
        tx_value = max(0, int(tx_value))
        inter = int(src_subnet_id) != int(dst_subnet_id)

        tariff_value = (tx_value * INTER_SUBNET_TARIFF_BPS // BPS_DENOM) if inter else 0
        lease_value = 0 if inter else (tx_value * INTRA_SUBNET_LEASE_BPS // BPS_DENOM)

        if collapse_guard or tx_value < (tariff_value + lease_value):
            routed = 0
        else:
            routed = tx_value - tariff_value - lease_value

        return TreasuryResult(
            inter_subnet=inter,
            tariff_value=tariff_value,
            lease_value=lease_value,
            routed_value=routed,
            treasury_credit=tariff_value if inter else 0,
        )

    def settle_governed(
        self,
        *,
        event_id: str,
        cap: Capability,
        subnet_scope: str,
        now_epoch_s: int,
        src_subnet_id: int,
        dst_subnet_id: int,
        tx_value: int,
        collapse_guard: bool,
        force_audit_fail: bool = False,
    ) -> TreasuryGovernedResult:
        settlement = self.settle(
            src_subnet_id=src_subnet_id,
            dst_subnet_id=dst_subnet_id,
            tx_value=tx_value,
            collapse_guard=collapse_guard,
        )
        staged_delta = {
            "domain": "treasury",
            "subnet_scope": str(subnet_scope),
            "src_subnet_id": int(src_subnet_id),
            "dst_subnet_id": int(dst_subnet_id),
            "tx_value": int(tx_value),
            "collapse_guard": bool(collapse_guard),
            "result": asdict(settlement),
        }

        mutation = self._coordinator.commit(
            event_id=str(event_id),
            cap=cap,
            required_right="TREASURY_TRANSFER",
            subnet_scope=str(subnet_scope),
            now_epoch_s=int(now_epoch_s),
            staged_delta=staged_delta,
            force_audit_fail=bool(force_audit_fail),
        )
        return TreasuryGovernedResult(
            ok=mutation.ok,
            code=mutation.code,
            committed=mutation.committed,
            event_id=mutation.event_id,
            settlement=settlement,
            detail=mutation.detail,
        )
