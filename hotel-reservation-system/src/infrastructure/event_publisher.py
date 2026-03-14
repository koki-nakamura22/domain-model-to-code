"""ログ出力イベントパブリッシャー。"""

from __future__ import annotations

import logging

from src.domain.events.events import DomainEvent

logger = logging.getLogger(__name__)


class LoggingEventPublisher:
    async def publish(self, event: DomainEvent) -> None:
        logger.info("Domain event published: %s - %s", type(event).__name__, event)
