from fastapi import APIRouter, Request
from models import AsyncSessionLocal, RawEvent
import os

router = APIRouter()

SECRET = os.getenv("SECRET_TOKEN", "demo-token-change-in-prod")

async def verify_token(request: Request):
    token = request.headers.get("X-Secret-Token")
    return token == SECRET

@router.post("/bitrix24")
async def bitrix24_webhook(request: Request):
    if not await verify_token(request):
        return {"ok": False, "error": "invalid token"}
    payload = await request.json()
    async with AsyncSessionLocal() as db:
        event = RawEvent(source="bitrix24", event_type=payload.get("event"), payload=payload)
        db.add(event)
        await db.commit()
    return {"ok": True}

@router.post("/uis")
async def uis_webhook(request: Request):
    if not await verify_token(request):
        return {"ok": False, "error": "invalid token"}
    payload = await request.json()
    async with AsyncSessionLocal() as db:
        event = RawEvent(source="uis", event_type=payload.get("event"), payload=payload)
        db.add(event)
        await db.commit()
    return {"ok": True}

@router.post("/1c")
async def one_c_webhook(request: Request):
    if not await verify_token(request):
        return {"ok": False, "error": "invalid token"}
    payload = await request.json()
    async with AsyncSessionLocal() as db:
        event = RawEvent(source="1c", event_type=payload.get("event"), payload=payload)
        db.add(event)
        await db.commit()
    return {"ok": True}
