"""
Роутер health-check.

Простой эндпоинт для проверки, что приложение отвечает.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    """Возвращает статус API."""
    return {"status": "ok"}
