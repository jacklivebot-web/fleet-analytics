"""
Роутер планировщика синхронизации.

Имитирует запуск синхронизации из внешних систем.
В продакшене здесь будет вызов реальных API Битрикс24, UIS и 1С.
"""

from fastapi import APIRouter
from models import AsyncSessionLocal, SyncState, select
from datetime import datetime, timezone
import asyncio

router = APIRouter()


async def _sync_source(source: str):
    """Обновляет метку времени последней успешной синхронизации для источника."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(SyncState).where(SyncState.source == source))
        state = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if state:
            state.last_success_at = now
        else:
            state = SyncState(source=source, last_success_at=now)
            db.add(state)
        await db.commit()
    return {"source": source, "synced_at": now.isoformat()}


@router.post("/bitrix24")
async def sync_bitrix24():
    """Имитирует синхронизацию с Битрикс24."""
    await asyncio.sleep(0.1)
    return await _sync_source("bitrix24")


@router.post("/uis")
async def sync_uis():
    """Имитирует синхронизацию с UIS."""
    await asyncio.sleep(0.1)
    return await _sync_source("uis")


@router.post("/1c")
async def sync_1c():
    """Имитирует синхронизацию с 1С."""
    await asyncio.sleep(0.1)
    return await _sync_source("1c")


@router.post("/all")
async def sync_all():
    """Запускает синхронизацию всех трёх источников."""
    results = []
    for source in ["bitrix24", "uis", "1c"]:
        results.append(await _sync_source(source))
    return {"scheduled": results}
