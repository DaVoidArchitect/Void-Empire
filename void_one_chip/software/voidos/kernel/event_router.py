from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .scheduler import DeterministicDomainScheduler, ScheduledIntent


@dataclass(frozen=True)
class RouteRecord:
    source_domain: str
    action: str
    target_domain: str
    endpoint_id: str


@dataclass(frozen=True)
class RoutedEvent:
    event_id: str
    source_domain: str
    action: str
    target_domain: str
    endpoint_id: str
    payload: dict[str, Any]


class EventRouter:
    """Deterministic route resolver and ordering helper."""

    def __init__(self, *, scheduler: DeterministicDomainScheduler | None = None) -> None:
        self._scheduler = scheduler or DeterministicDomainScheduler()
        self._routes: dict[tuple[str, str], RouteRecord] = {}

    def add_route(self, *, source_domain: str, action: str, target_domain: str, endpoint_id: str) -> None:
        key = (str(source_domain), str(action))
        self._routes[key] = RouteRecord(
            source_domain=str(source_domain),
            action=str(action),
            target_domain=str(target_domain),
            endpoint_id=str(endpoint_id),
        )

    def route(
        self,
        *,
        event_id: str,
        source_domain: str,
        action: str,
        payload: dict[str, Any],
    ) -> tuple[bool, str, RoutedEvent | None]:
        key = (str(source_domain), str(action))
        route = self._routes.get(key)
        if route is None:
            return (False, "E_POLICY_BLOCKED", None)

        routed = RoutedEvent(
            event_id=str(event_id),
            source_domain=route.source_domain,
            action=route.action,
            target_domain=route.target_domain,
            endpoint_id=route.endpoint_id,
            payload=dict(payload),
        )
        return (True, "OK", routed)

    def order_dispatches(
        self,
        *,
        subnet_scope: str,
        routed_events: list[RoutedEvent],
    ) -> list[RoutedEvent]:
        intents = [
            ScheduledIntent(
                domain_id=ev.target_domain,
                subnet_scope=str(subnet_scope),
                monotonic_counter=idx + 1,
                pulse_id=ev.event_id,
                payload={
                    "endpoint_id": ev.endpoint_id,
                    "source_domain": ev.source_domain,
                    "action": ev.action,
                    "payload": dict(ev.payload),
                },
            )
            for idx, ev in enumerate(routed_events)
        ]
        ordered = self._scheduler.order(intents)

        by_event_id = {ev.event_id: ev for ev in routed_events}
        return [by_event_id[i.pulse_id] for i in ordered if i.pulse_id in by_event_id]

    def snapshot_routes(self) -> dict[str, dict[str, str]]:
        return {
            f"{src}:{act}": {
                "source_domain": rec.source_domain,
                "action": rec.action,
                "target_domain": rec.target_domain,
                "endpoint_id": rec.endpoint_id,
            }
            for (src, act), rec in sorted(self._routes.items())
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "route_count": len(self._routes),
            "routes": self.snapshot_routes(),
        }
