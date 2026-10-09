from fastapi import APIRouter
from models import AsyncSessionLocal, SyncState, select
from datetime import datetime, timezone
import asyncio

router = APIRouter()

async def _sync_source(source: str):
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
    await asyncio.sleep(0.1)
    return await _sync_source("bitrix24")

@router.post("/uis")
async def sync_uis():
    await asyncio.sleep(0.1)
    return await _sync_source("uis")

@router.post("/1c")
async def sync_1c():
    await asyncio.sleep(0.1)
    return await _sync_source("1c")

@router.post("/all")
async def sync_all():
    results = []
    for source in ["bitrix24", "uis", "1c"]:
        results.append(await _sync_source(source))
    return {"scheduled": results}
