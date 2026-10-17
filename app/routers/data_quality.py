"""
Роутер проверки качества данных.

Выполняет 13 автоматических проверок, которые находят дубли,
пропуски, аномалии и расхождения между CRM, телефонией и данными парка.

Эндпоинт используется для быстрой диагностики: перед отчётом проверяем,
нет ли грязи, которая сломает цифры.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from models import get_db

router = APIRouter()


@router.get("/")
async def data_quality(db: AsyncSession = Depends(get_db)):
    """
    Возвращает сводку качества данных с общей оценкой overall.

    Severity:
    - error: критичная проблема, требует исправления;
    - warning: подозрительные данные, стоит проверить;
    - info: наблюдение, не обязательно проблема;
    - ok: всё хорошо.
    """
    checks = {}

    # 1. Дубли контактов по телефону
    r = await db.execute(text("""
        select phone_normalized, count(*) as cnt
        from crm_contacts
        where phone_normalized is not null
        group by phone_normalized
        having count(*) > 1
    """))
    rows = r.mappings().all()
    checks["duplicate_contacts_by_phone"] = {
        "description": "Контакты с одинаковым нормализованным телефоном",
        "count": len(rows),
        "examples": [dict(x) for x in rows[:5]],
        "severity": "warning" if rows else "ok",
    }

    # 2. Звонки без привязки к сделке и контакту
    r = await db.execute(text("""
        select count(*) as cnt from calls
        where deal_id is null and contact_id is null
    """))
    cnt = r.scalar()
    checks["calls_without_deal_and_contact"] = {
        "description": "Звонки, не привязанные ни к сделке, ни к контакту",
        "count": int(cnt),
        "severity": "warning" if cnt > 0 else "ok",
    }

    # 3. Сделки без звонков
    r = await db.execute(text("""
        select count(*) as cnt from crm_deals d
        where not exists (select 1 from calls c where c.deal_id = d.id)
    """))
    cnt = r.scalar()
    checks["deals_without_calls"] = {
        "description": "Сделки, к которым не привязан ни один звонок",
        "count": int(cnt),
        "severity": "info",
    }

    # 4. Заказы без связанной сделки
    r = await db.execute(text("""
        select count(*) as cnt from transport_orders
        where deal_id is null
    """))
    cnt = r.scalar()
    checks["orders_without_deal"] = {
        "description": "Заказы без связанной сделки",
        "count": int(cnt),
        "severity": "warning" if cnt > 0 else "ok",
    }

    # 5. Заказы без ТС или водителя
    r = await db.execute(text("""
        select count(*) as cnt from transport_orders
        where vehicle_id is null or driver_id is null
    """))
    cnt = r.scalar()
    checks["orders_without_vehicle_or_driver"] = {
        "description": "Заказы без автомобиля или водителя",
        "count": int(cnt),
        "severity": "error" if cnt > 0 else "ok",
    }

    # 6. Отрицательная выручка или затраты
    r = await db.execute(text("""
        select count(*) as cnt from transport_orders
        where revenue < 0 or cost < 0
    """))
    cnt = r.scalar()
    checks["negative_revenue_or_cost"] = {
        "description": "Заказы с отрицательной выручкой или затратами",
        "count": int(cnt),
        "severity": "error" if cnt > 0 else "ok",
    }

    # 7. Автомобили без заказов
    r = await db.execute(text("""
        select count(*) as cnt from vehicles v
        where not exists (select 1 from transport_orders o where o.vehicle_id = v.id)
    """))
    cnt = r.scalar()
    checks["vehicles_without_orders"] = {
        "description": "Автомобили без заказов",
        "count": int(cnt),
        "severity": "info",
    }

    # 8. Автомобили без ремонта и заправки
    r = await db.execute(text("""
        select count(*) as cnt from vehicles v
        where not exists (select 1 from repairs r where r.vehicle_id = v.id)
          and not exists (select 1 from fuel_transactions f where f.vehicle_id = v.id)
    """))
    cnt = r.scalar()
    checks["vehicles_without_repairs_and_fuel"] = {
        "description": "Автомобили без записей о ремонте и заправке",
        "count": int(cnt),
        "severity": "info",
    }

    # 9. Аномальный расход топлива
    r = await db.execute(text("""
        select vehicle_id, plate, liters_per_100km
        from mart_vehicle_fuel_efficiency
        where liters_per_100km > 100 or liters_per_100km < 0
    """))
    rows = r.mappings().all()
    checks["fuel_consumption_anomalies"] = {
        "description": "Аномальные значения расхода топлива (>100 или <0 л/100км)",
        "count": len(rows),
        "examples": [dict(x) for x in rows[:5]],
        "severity": "warning" if rows else "ok",
    }

    # 10. Доля пропущенных звонков
    r = await db.execute(text("""
        select
            count(*) filter (where status = 'missed') as missed,
            count(*) as total,
            round(
                count(*) filter (where status = 'missed')::numeric
                / nullif(count(*), 0) * 100,
                2
            ) as missed_percent
        from calls
    """))
    row = dict(r.mappings().first())
    checks["missed_calls_ratio"] = {
        "description": "Доля пропущенных звонков",
        "value": row,
        "severity": "warning" if (row.get("missed_percent") or 0) > 50 else "ok",
    }

    # 11. Аномальная длительность звонков
    r = await db.execute(text("""
        select count(*) as cnt from calls
        where duration_sec > 7200 or duration_sec < 0
    """))
    cnt = r.scalar()
    checks["call_duration_anomalies"] = {
        "description": "Звонки с аномальной длительностью (>2ч или <0)",
        "count": int(cnt),
        "severity": "warning" if cnt > 0 else "ok",
    }

    # 12. Выигранные сделки без выданного заказа
    r = await db.execute(text("""
        select count(*) as cnt from crm_deals d
        where d.stage_id = 'won'
          and not exists (select 1 from transport_orders o where o.deal_id = d.id)
    """))
    cnt = r.scalar()
    checks["won_deals_without_order"] = {
        "description": "Выигранные сделки без выданного автомобиля",
        "count": int(cnt),
        "severity": "warning" if cnt > 0 else "ok",
    }

    # 13. Ремонты с отрицательной длительностью
    r = await db.execute(text("""
        select count(*) as cnt from repairs
        where ended_at < started_at
    """))
    cnt = r.scalar()
    checks["repairs_negative_duration"] = {
        "description": "Ремонты с отрицательной длительностью",
        "count": int(cnt),
        "severity": "error" if cnt > 0 else "ok",
    }

    # Итоговая оценка
    severities = [v["severity"] for v in checks.values()]
    overall = "ok"
    if "error" in severities:
        overall = "error"
    elif "warning" in severities:
        overall = "warning"

    return {
        "overall": overall,
        "checks": checks,
    }
