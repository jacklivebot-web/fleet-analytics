from fastapi import APIRouter, Request
from models import AsyncSessionLocal, RawEvent

router = APIRouter()

@router.post("/bitrix24")
async def bitrix24_webhook(request: Request):
    payload = await request.json()
    async with AsyncSessionLocal() as db:
        event = RawEvent(source="bitrix24", event_type=payload.get("event"), payload=payload)
        db.add(event)
        await db.commit()
    return {"ok": True}

@router.post("/uis")
async def uis_webhook(request: Request):
    payload = await request.json()
    async with AsyncSessionLocal() as db:
        event = RawEvent(source="uis", event_type=payload.get("event"), payload=payload)
        db.add(event)
        await db.commit()
    return {"ok": True}

@router.post("/1c")
async def one_c_webhook(request: Request):
    payload = await request.json()
    async with AsyncSessionLocal() as db:
        event = RawEvent(source="1c", event_type=payload.get("event"), payload=payload)
        db.add(event)
        await db.commit()
    return {"ok": True}
