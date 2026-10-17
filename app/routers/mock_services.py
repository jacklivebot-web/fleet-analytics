"""
Mock-роутеры для имитации внешних систем.

Используются в MVP как замена реальных API Битрикс24, UIS и 1С.
Позволяют фронтенду и тестам получать данные в том же формате,
в каком их бы отдавали реальные интеграции.
"""

from fastapi import APIRouter
from models import AsyncSessionLocal, CRMContact, CRMDeal, Call, Vehicle, TransportOrder
from sqlalchemy import select

router = APIRouter()


@router.get("/bitrix/deals")
async def mock_bitrix_deals():
    """Возвращает до 10 последних сделок в формате, похожем на Битрикс24."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(CRMDeal).limit(10))
        rows = result.scalars().all()
    return [
        {
            "id": r.bitrix_id,
            "title": r.title,
            "stage_id": r.stage_id,
            "amount": float(r.amount) if r.amount else None,
            "contact_id": r.contact_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/bitrix/contacts")
async def mock_bitrix_contacts():
    """Возвращает до 10 последних контактов в формате Битрикс24."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(CRMContact).limit(10))
        rows = result.scalars().all()
    return [
        {
            "id": r.bitrix_id,
            "name": r.name,
            "phone": r.phone_normalized,
            "email": r.email,
        }
        for r in rows
    ]


@router.get("/uis/calls")
async def mock_uis_calls():
    """Возвращает до 20 последних звонков в формате UIS."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Call).limit(20))
        rows = result.scalars().all()
    return [
        {
            "call_id": r.provider_call_id,
            "phone": r.phone_normalized,
            "direction": r.direction,
            "status": r.status,
            "duration_sec": r.duration_sec,
            "started_at": r.started_at.isoformat() if r.started_at else None,
        }
        for r in rows
    ]


@router.get("/1c/vehicles")
async def mock_1c_vehicles():
    """Возвращает до 20 последних автомобилей в формате 1С."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Vehicle).limit(20))
        rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "plate": r.plate,
            "model": r.model,
            "year": r.year,
            "status": r.status,
        }
        for r in rows
    ]


@router.get("/1c/orders")
async def mock_1c_orders():
    """Возвращает до 20 последних заказов в формате 1С."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(TransportOrder).limit(20))
        rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "vehicle_id": r.vehicle_id,
            "driver_id": r.driver_id,
            "route_name": r.route_name,
            "revenue": float(r.revenue) if r.revenue else None,
            "cost": float(r.cost) if r.cost else None,
            "status": r.status,
        }
        for r in rows
    ]
