from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models import get_db, select, CRMContact, CRMDeal, Call, Vehicle, Driver, TransportOrder, SyncState
import random
from datetime import datetime, timedelta, timezone

router = APIRouter()

def normalize_phone(phone: str) -> str:
    digits = "".join(c for c in phone if c.isdigit())
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    return digits

@router.post("/generate")
async def generate_data(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    contacts = []
    for i in range(50):
        phone = normalize_phone(f"+79{random.randint(100000000, 999999999)}")
        c = CRMContact(
            id=i+1,
            bitrix_id=1000+i+1,
            name=f"Клиент {i+1}",
            phone_normalized=phone,
            email=f"client{i+1}@example.com",
            source_updated_at=now,
            raw_data={}
        )
        contacts.append(c)
    db.add_all(contacts)

    deals = []
    for i in range(100):
        contact = contacts[i % len(contacts)]
        created = now - timedelta(days=random.randint(1, 120))
        d = CRMDeal(
            id=i+1,
            bitrix_id=2000+i+1,
            title=f"Сделка {i+1}",
            stage_id=random.choice(["new", "in_progress", "won", "lost"]),
            pipeline_id="transport",
            amount=random.randint(5000, 200000),
            responsible_id=random.randint(1, 5),
            contact_id=contact.id,
            company_id=None,
            created_at=created,
            closed_at=created + timedelta(days=random.randint(1, 30)) if random.random() > 0.5 else None,
            raw_data={}
        )
        deals.append(d)
    db.add_all(deals)

    vehicles = []
    for i in range(30):
        v = Vehicle(
            id=i+1,
            plate=f"А{random.randint(100, 999)}БВ{random.randint(10, 99)}",
            model=random.choice(["КамАЗ 5490", "Volvo FH", "MAN TGX", "Scania R"]),
            year=random.randint(2015, 2024),
            status=random.choice(["active", "repair", "idle"])
        )
        vehicles.append(v)
    db.add_all(vehicles)

    drivers = []
    for i in range(40):
        phone = normalize_phone(f"+79{random.randint(100000000, 999999999)}")
        dr = Driver(
            id=i+1,
            name=f"Водитель {i+1}",
            phone_normalized=phone,
            license_category=random.choice(["C", "CE", "D"])
        )
        drivers.append(dr)
    db.add_all(drivers)
    await db.flush()

    vehicle_ids = [v.id for v in vehicles]
    driver_ids = [d.id for d in drivers]

    orders = []
    for i in range(80):
        deal = deals[i % len(deals)]
        planned = now - timedelta(days=random.randint(1, 90))
        o = TransportOrder(
            id=i+1,
            deal_id=deal.id,
            vehicle_id=random.choice(vehicle_ids),
            driver_id=random.choice(driver_ids),
            route_name=random.choice(["Москва — Санкт-Петербург", "Казань — Нижний Новгород", "Екатеринбург — Тюмень"]),
            planned_start=planned,
            actual_end=planned + timedelta(hours=random.randint(4, 48)),
            revenue=random.randint(10000, 500000),
            cost=random.randint(5000, 300000),
            status=random.choice(["completed", "in_progress", "cancelled"])
        )
        orders.append(o)
    db.add_all(orders)

    calls = []
    statuses = ["answered", "missed", "busy"]
    directions = ["inbound", "outbound"]
    for i in range(500):
        contact = contacts[i % len(contacts)]
        deal = deals[i % len(deals)]
        started = now - timedelta(days=random.randint(1, 90), minutes=random.randint(0, 1440))
        duration = random.randint(20, 600) if random.random() > 0.2 else 0
        c = Call(
            id=i+1,
            provider="uis",
            provider_call_id=f"call-{i+1}",
            direction=random.choice(directions),
            phone_normalized=contact.phone_normalized,
            employee_id=random.randint(1, 20),
            contact_id=contact.id,
            deal_id=deal.id,
            started_at=started,
            answered_at=started + timedelta(seconds=random.randint(1, 20)) if duration else None,
            ended_at=started + timedelta(seconds=duration) if duration else started + timedelta(seconds=random.randint(5, 30)),
            duration_sec=duration,
            wait_duration_sec=random.randint(0, 60),
            status=random.choice(statuses),
            raw_data={}
        )
        calls.append(c)
    db.add_all(calls)

    for source in ["bitrix24", "uis", "1c"]:
        s = SyncState(source=source, last_success_at=now - timedelta(days=1))
        db.add(s)

    await db.commit()
    return {
        "contacts": len(contacts),
        "deals": len(deals),
        "vehicles": len(vehicles),
        "drivers": len(drivers),
        "orders": len(orders),
        "calls": len(calls)
    }


@router.get("/state")
async def sync_state(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SyncState))
    rows = result.scalars().all()
    return [{"source": r.source, "last_success_at": r.last_success_at} for r in rows]
