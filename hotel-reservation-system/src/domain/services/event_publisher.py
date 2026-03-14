"""イベントパブリッシャーProtocol。"""

from __future__ import annotations

from typing import Protocol

from src.domain.events.events import DomainEvent


class EventPublisher(Protocol):
    async def publish(self, event: DomainEvent) -> None: ...
