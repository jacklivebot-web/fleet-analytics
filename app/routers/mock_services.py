from fastapi import APIRouter
from models import AsyncSessionLocal, CRMContact, CRMDeal, Call, Vehicle, Driver, TransportOrder
from sqlalchemy import select
from datetime import datetime, timezone
import random

router = APIRouter()

@router.get("/bitrix/deals")
async def mock_bitrix_deals():
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
