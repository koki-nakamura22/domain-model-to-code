"""FastAPI アプリケーション エントリポイント。"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.infrastructure.persistence.database import engine
from src.infrastructure.persistence.models.db_models import Base
from src.presentation.api.routers import admin_router, guest_router, payment_router, reservation_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Hotel Reservation System",
    description="Domain model to code demo - Hotel Reservation System API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(guest_router)
app.include_router(reservation_router)
app.include_router(payment_router)
app.include_router(admin_router)
