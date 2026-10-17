"""
Webhook-роутеры.

Принимают события из внешних систем: Битрикс24, UIS, 1С.
Каждое событие сохраняется в raw_events для аудита и возможности
повторной обработки задним числом.

Авторизация по токену из заголовка X-Secret-Token.
"""

from fastapi import APIRouter, Request
from models import AsyncSessionLocal, RawEvent
import os

router = APIRouter()

SECRET = os.getenv("SECRET_TOKEN", "demo-token-change-in-prod")


async def verify_token(request: Request) -> bool:
    """Проверяет секретный токен в заголовке X-Secret-Token."""
    token = request.headers.get("X-Secret-Token")
    return token == SECRET


async def _save_event(source: str, payload: dict):
    """Сохраняет входящее событие в таблицу raw_events."""
    async with AsyncSessionLocal() as db:
        event = RawEvent(
            source=source,
            event_type=payload.get("event"),
            payload=payload,
        )
        db.add(event)
        await db.commit()


@router.post("/bitrix24")
async def bitrix24_webhook(request: Request):
    """Принимает webhook-события из Битрикс24."""
    if not await verify_token(request):
        return {"ok": False, "error": "invalid token"}
    payload = await request.json()
    await _save_event("bitrix24", payload)
    return {"ok": True}


@router.post("/uis")
async def uis_webhook(request: Request):
    """Принимает webhook-события из UIS."""
    if not await verify_token(request):
        return {"ok": False, "error": "invalid token"}
    payload = await request.json()
    await _save_event("uis", payload)
    return {"ok": True}


@router.post("/1c")
async def one_c_webhook(request: Request):
    """Принимает webhook-события из 1С."""
    if not await verify_token(request):
        return {"ok": False, "error": "invalid token"}
    payload = await request.json()
    await _save_event("1c", payload)
    return {"ok": True}
