"""
Роутер генерации синтетических данных.

Создаёт тестовый набор данных для демонстрации платформы:
контакты, сделки, автомобили, водители, заказы, звонки,
ремонты и заправки.

Повторный вызов без force возвращает текущие объёмы — это удобно
для тестов и быстрого старта.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from models import (
    get_db, select, CRMContact, CRMDeal, Call, Vehicle, Driver,
    TransportOrder, SyncState, AsyncSessionLocal, Repair, FuelTransaction,
)
from sqlalchemy import text
import random
from datetime import datetime, timedelta, timezone

router = APIRouter()


def normalize_phone(phone: str) -> str:
    """Приводит телефон к формату 11 цифр, начинающихся с 7."""
    digits = "".join(c for c in phone if c.isdigit())
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    return digits


@router.post("/generate")
async def generate_data(
    force: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """
    Генерирует синтетические данные для демонстрации.

    Если данные уже есть и force=false, возвращает текущие объёмы.
    Это делает эндпоинт идемпотентным для тестов и быстрого старта.
    """
    result = await db.execute(select(CRMContact))
    existing = result.scalars().first()
    if existing and not force:
        counts = await db.execute(text("""
            select
                (select count(*) from crm_contacts) as contacts,
                (select count(*) from crm_deals) as deals,
                (select count(*) from vehicles) as vehicles,
                (select count(*) from drivers) as drivers,
                (select count(*) from transport_orders) as orders,
                (select count(*) from calls) as calls,
                (select count(*) from repairs) as repairs,
                (select count(*) from fuel_transactions) as fuel_transactions
        """))
        row = counts.mappings().first()
        return dict(row)

    # Полная очистка перед перегенерацией
    await db.execute(text("""
        TRUNCATE TABLE crm_contacts, crm_deals, vehicles, drivers,
        transport_orders, calls, repairs, fuel_transactions, sync_state
        RESTART IDENTITY CASCADE
    """))
    await db.commit()

    now = datetime.now(timezone.utc)

    # --- Контакты из CRM ---
    contacts = []
    for i in range(50):
        phone = normalize_phone(f"+79{random.randint(100000000, 999999999)}")
        contacts.append(CRMContact(
            id=i + 1,
            bitrix_id=1000 + i + 1,
            name=f"Клиент {i + 1}",
            phone_normalized=phone,
            email=f"client{i + 1}@example.com",
            source_updated_at=now,
            raw_data={},
        ))
    db.add_all(contacts)

    # --- Сделки из CRM ---
    deals = []
    for i in range(100):
        contact = contacts[i % len(contacts)]
        created = now - timedelta(days=random.randint(1, 120))
        deals.append(CRMDeal(
            id=i + 1,
            bitrix_id=2000 + i + 1,
            title=f"Сделка {i + 1}",
            stage_id=random.choice(["new", "in_progress", "won", "lost"]),
            pipeline_id="transport",
            amount=random.randint(5000, 200000),
            responsible_id=random.randint(1, 5),
            contact_id=contact.id,
            company_id=None,
            created_at=created,
            closed_at=(
                created + timedelta(days=random.randint(1, 30))
                if random.random() > 0.5 else None
            ),
            raw_data={},
        ))
    db.add_all(deals)

    # --- Автомобили из 1С ---
    vehicles = []
    for i in range(30):
        vehicles.append(Vehicle(
            id=i + 1,
            plate=f"А{random.randint(100, 999)}БВ{random.randint(10, 99)}",
            model=random.choice(["КамАЗ 5490", "Volvo FH", "MAN TGX", "Scania R"]),
            year=random.randint(2015, 2024),
            status=random.choice(["active", "repair", "idle"]),
        ))
    db.add_all(vehicles)

    # --- Водители ---
    drivers = []
    for i in range(40):
        phone = normalize_phone(f"+79{random.randint(100000000, 999999999)}")
        drivers.append(Driver(
            id=i + 1,
            name=f"Водитель {i + 1}",
            phone_normalized=phone,
            license_category=random.choice(["C", "CE", "D"]),
        ))
    db.add_all(drivers)
    await db.flush()

    vehicle_ids = [v.id for v in vehicles]
    driver_ids = [d.id for d in drivers]

    # --- Ремонты ТС ---
    repairs = []
    for i in range(60):
        vehicle = random.choice(vehicles)
        start = now - timedelta(days=random.randint(1, 365))
        end = start + timedelta(days=random.randint(1, 14))
        repairs.append(Repair(
            id=i + 1,
            vehicle_id=vehicle.id,
            started_at=start,
            ended_at=end,
            cost=random.randint(1000, 50000),
            description=random.choice([
                "ТО", "Ремонт двигателя", "Замена шин", "Кузовной ремонт",
            ]),
        ))
    db.add_all(repairs)

    # --- Заправки ---
    fuel_transactions = []
    for i in range(200):
        vehicle = random.choice(vehicles)
        driver = random.choice(drivers)
        odometer = random.randint(50000, 300000)
        liters = round(random.uniform(30, 300), 2)
        fuel_transactions.append(FuelTransaction(
            id=i + 1,
            vehicle_id=vehicle.id,
            driver_id=driver.id,
            liters=liters,
            cost=round(liters * random.uniform(45, 60), 2),
            odometer_km=odometer,
            created_at=now - timedelta(days=random.randint(1, 365)),
        ))
    db.add_all(fuel_transactions)

    # --- Заказы на перевозку ---
    orders = []
    for i in range(80):
        deal = deals[i % len(deals)]
        planned = now - timedelta(days=random.randint(1, 90))
        orders.append(TransportOrder(
            id=i + 1,
            deal_id=deal.id,
            vehicle_id=random.choice(vehicle_ids),
            driver_id=random.choice(driver_ids),
            route_name=random.choice([
                "Москва — Санкт-Петербург",
                "Казань — Нижний Новгород",
                "Екатеринбург — Тюмень",
            ]),
            planned_start=planned,
            actual_end=planned + timedelta(hours=random.randint(4, 48)),
            revenue=random.randint(10000, 500000),
            cost=random.randint(5000, 300000),
            status=random.choice(["completed", "in_progress", "cancelled"]),
        ))
    db.add_all(orders)

    # --- Звонки из UIS ---
    calls = []
    statuses = ["answered", "missed", "busy"]
    directions = ["inbound", "outbound"]
    for i in range(500):
        contact = contacts[i % len(contacts)]
        deal = deals[i % len(deals)]
        started = now - timedelta(
            days=random.randint(1, 90),
            minutes=random.randint(0, 1440),
        )
        duration = random.randint(20, 600) if random.random() > 0.2 else 0
        calls.append(Call(
            id=i + 1,
            provider="uis",
            provider_call_id=f"call-{i + 1}",
            direction=random.choice(directions),
            phone_normalized=contact.phone_normalized,
            employee_id=random.randint(1, 20),
            contact_id=contact.id,
            deal_id=deal.id,
            started_at=started,
            answered_at=(
                started + timedelta(seconds=random.randint(1, 20))
                if duration else None
            ),
            ended_at=(
                started + timedelta(seconds=duration)
                if duration else started + timedelta(seconds=random.randint(5, 30))
            ),
            duration_sec=duration,
            wait_duration_sec=random.randint(0, 60),
            status=random.choice(statuses),
            raw_data={},
        ))
    db.add_all(calls)

    # --- Состояние синхронизации ---
    for source in ["bitrix24", "uis", "1c"]:
        db.add(SyncState(source=source, last_success_at=now - timedelta(days=1)))

    await db.commit()
    return {
        "contacts": len(contacts),
        "deals": len(deals),
        "vehicles": len(vehicles),
        "drivers": len(drivers),
        "orders": len(orders),
        "calls": len(calls),
        "repairs": len(repairs),
        "fuel_transactions": len(fuel_transactions),
    }


@router.get("/state")
async def sync_state():
    """Возвращает время последней успешной синхронизации по каждому источнику."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(SyncState))
        rows = result.scalars().all()
    return [
        {"source": r.source, "last_success_at": r.last_success_at}
        for r in rows
    ]
