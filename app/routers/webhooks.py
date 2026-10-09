from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models import get_db, RawEvent

router = APIRouter()

@router.post("/bitrix24")
async def bitrix24_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.json()
    event = RawEvent(source="bitrix24", event_type=payload.get("event"), payload=payload)
    db.add(event)
    await db.commit()
    return {"ok": True}

@router.post("/uis")
async def uis_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.json()
    event = RawEvent(source="uis", event_type=payload.get("event"), payload=payload)
    db.add(event)
    await db.commit()
    return {"ok": True}

@router.post("/1c")
async def one_c_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.json()
    event = RawEvent(source="1c", event_type=payload.get("event"), payload=payload)
    db.add(event)
    await db.commit()
    return {"ok": True}
