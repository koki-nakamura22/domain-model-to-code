"""イベントディスパッチャー付きパブリッシャー。"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

from src.domain.events.events import DomainEvent

logger = logging.getLogger(__name__)

EventHandler = Callable[[Any], Coroutine[Any, Any, None]]


class DispatchingEventPublisher:
    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        logger.info("Domain event published: %s - %s", type(event).__name__, event)
        for handler in self._handlers[type(event)]:
            await handler(event)
