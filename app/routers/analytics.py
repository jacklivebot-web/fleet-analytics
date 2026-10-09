from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from models import get_db

router = APIRouter()

CALCULATIONS = {
    "call_conversion": {
        "description": "Доля звонков, связанных со сделкой (deal_id is not null), от общего числа звонков за месяц.",
        "formula": "calls_with_deal / calls * 100",
        "sql": """
            select
                date_trunc('month', c.started_at)::text as period,
                count(distinct c.id) as calls,
                count(distinct c.deal_id) as calls_with_deal,
                round(count(distinct c.deal_id)::numeric / nullif(count(distinct c.id), 0) * 100, 2) as conversion_percent
            from calls c
            where c.started_at >= current_date - interval '12 months'
            group by 1
            order by 1
        """,
    },
    "vehicle_efficiency": {
        "description": "Экономический результат автомобиля: выручка и затраты по заказам, прибыль = выручка - затраты.",
        "formula": "profit = total_revenue - total_cost",
        "sql": """
            select
                v.id as vehicle_id,
                v.plate,
                v.model,
                count(o.id) as orders_count,
                coalesce(sum(o.revenue), 0) as total_revenue,
                coalesce(sum(o.cost), 0) as total_cost,
                coalesce(sum(o.revenue), 0) - coalesce(sum(o.cost), 0) as profit
            from vehicles v
            left join transport_orders o on o.vehicle_id = v.id
            group by v.id, v.plate, v.model
            order by profit desc
        """,
    },
    "order_profitability": {
        "description": "Прибыльность заказа: разница между выручкой и затратами, маржа = прибыль / выручка * 100.",
        "formula": "profit = revenue - cost; margin_percent = profit / revenue * 100",
        "sql": """
            select
                o.id as order_id,
                d.title as deal_title,
                o.route_name,
                o.revenue,
                o.cost,
                o.revenue - o.cost as profit,
                case when o.revenue > 0 then round((o.revenue - o.cost) / o.revenue * 100, 2) else 0 end as margin_percent,
                o.status
            from transport_orders o
            left join crm_deals d on d.id = o.deal_id
            order by profit desc
        """,
    },
    "vehicle_downtime": {
        "description": "Количество дней простоя и ремонта автомобиля за последние 12 месяцев.",
        "formula": "downtime_days = sum(repair_duration_days); repair_cost = sum(repair_cost)",
        "sql": """
            select
                v.id as vehicle_id,
                v.plate,
                v.model,
                count(r.id) as repairs_count,
                coalesce(sum(extract(epoch from (r.ended_at - r.started_at)) / 86400), 0) as downtime_days,
                coalesce(sum(r.cost), 0) as repair_cost
            from vehicles v
            left join repairs r on r.vehicle_id = v.id
                and r.started_at >= current_date - interval '12 months'
            group by v.id, v.plate, v.model
            order by downtime_days desc
        """,
    },
    "vehicle_fuel_efficiency": {
        "description": "Средний расход топлива на 100 км по заправкам.",
        "formula": "fuel_per_100km = liters / (max_odometer - min_odometer) * 100",
        "sql": """
            select
                v.id as vehicle_id,
                v.plate,
                v.model,
                count(ft.id) as refuels_count,
                coalesce(sum(ft.liters), 0) as total_liters,
                coalesce(sum(ft.cost), 0) as fuel_cost,
                case
                    when (max(ft.odometer_km) - min(ft.odometer_km)) > 0
                    then round(sum(ft.liters) / (max(ft.odometer_km) - min(ft.odometer_km)) * 100, 2)
                    else 0
                end as liters_per_100km
            from vehicles v
            left join fuel_transactions ft on ft.vehicle_id = v.id
            group by v.id, v.plate, v.model
            order by liters_per_100km desc
        """,
    },
    "customer_ltv": {
        "description": "Пожизненная ценность клиента = сумма выручки по всем его сделкам и заказам.",
        "formula": "ltv = sum(order_revenue); deal_count = count(deals); order_count = count(orders)",
        "sql": """
            select
                c.id as contact_id,
                c.name,
                c.phone_normalized,
                count(distinct d.id) as deals_count,
                count(distinct o.id) as orders_count,
                coalesce(sum(o.revenue), 0) as ltv,
                coalesce(sum(o.revenue - o.cost), 0) as profit
            from crm_contacts c
            left join crm_deals d on d.contact_id = c.id
            left join transport_orders o on o.deal_id = d.id
            group by c.id, c.name, c.phone_normalized
            order by ltv desc
        """,
    },
}


@router.post("/recalc")
async def recalc_marts(db: AsyncSession = Depends(get_db)):
    # 1. mart_call_conversion
    await db.execute(text("""
        create table if not exists mart_call_conversion (
            id serial primary key,
            period text not null,
            calls integer,
            calls_with_deal integer,
            conversion_percent numeric(5,2)
        )
    """))
    await db.execute(text("delete from mart_call_conversion"))
    await db.execute(text(f"""
        insert into mart_call_conversion (period, calls, calls_with_deal, conversion_percent)
        {CALCULATIONS['call_conversion']['sql']}
    """))

    # 2. mart_vehicle_efficiency
    await db.execute(text("""
        create table if not exists mart_vehicle_efficiency (
            id serial primary key,
            vehicle_id bigint,
            plate text,
            model text,
            orders_count integer,
            total_revenue numeric(15,2),
            total_cost numeric(15,2),
            profit numeric(15,2)
        )
    """))
    await db.execute(text("delete from mart_vehicle_efficiency"))
    await db.execute(text(f"""
        insert into mart_vehicle_efficiency (vehicle_id, plate, model, orders_count, total_revenue, total_cost, profit)
        {CALCULATIONS['vehicle_efficiency']['sql']}
    """))

    # 3. mart_order_profitability
    await db.execute(text("""
        create table if not exists mart_order_profitability (
            id serial primary key,
            order_id bigint,
            deal_title text,
            route_name text,
            revenue numeric(15,2),
            cost numeric(15,2),
            profit numeric(15,2),
            margin_percent numeric(6,2),
            status text
        )
    """))
    await db.execute(text("delete from mart_order_profitability"))
    await db.execute(text(f"""
        insert into mart_order_profitability (order_id, deal_title, route_name, revenue, cost, profit, margin_percent, status)
        {CALCULATIONS['order_profitability']['sql']}
    """))

    # 4. mart_vehicle_downtime
    await db.execute(text("""
        create table if not exists mart_vehicle_downtime (
            id serial primary key,
            vehicle_id bigint,
            plate text,
            model text,
            repairs_count integer,
            downtime_days numeric(10,2),
            repair_cost numeric(15,2)
        )
    """))
    await db.execute(text("delete from mart_vehicle_downtime"))
    await db.execute(text(f"""
        insert into mart_vehicle_downtime (vehicle_id, plate, model, repairs_count, downtime_days, repair_cost)
        {CALCULATIONS['vehicle_downtime']['sql']}
    """))

    # 5. mart_vehicle_fuel_efficiency
    await db.execute(text("""
        create table if not exists mart_vehicle_fuel_efficiency (
            id serial primary key,
            vehicle_id bigint,
            plate text,
            model text,
            refuels_count integer,
            total_liters numeric(12,2),
            fuel_cost numeric(15,2),
            liters_per_100km numeric(6,2)
        )
    """))
    await db.execute(text("delete from mart_vehicle_fuel_efficiency"))
    await db.execute(text(f"""
        insert into mart_vehicle_fuel_efficiency (vehicle_id, plate, model, refuels_count, total_liters, fuel_cost, liters_per_100km)
        {CALCULATIONS['vehicle_fuel_efficiency']['sql']}
    """))

    # 6. mart_customer_ltv
    await db.execute(text("""
        create table if not exists mart_customer_ltv (
            id serial primary key,
            contact_id bigint,
            name text,
            phone_normalized text,
            deals_count integer,
            orders_count integer,
            ltv numeric(15,2),
            profit numeric(15,2)
        )
    """))
    await db.execute(text("delete from mart_customer_ltv"))
    await db.execute(text(f"""
        insert into mart_customer_ltv (contact_id, name, phone_normalized, deals_count, orders_count, ltv, profit)
        {CALCULATIONS['customer_ltv']['sql']}
    """))

    await db.commit()
    return {"ok": True}


@router.get("/call-conversion")
async def call_conversion(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("select * from mart_call_conversion"))
    rows = result.mappings().all()
    return [dict(r) for r in rows]


@router.get("/vehicle-efficiency")
async def vehicle_efficiency(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("select * from mart_vehicle_efficiency"))
    rows = result.mappings().all()
    return [dict(r) for r in rows]


@router.get("/order-profitability")
async def order_profitability(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("select * from mart_order_profitability"))
    rows = result.mappings().all()
    return [dict(r) for r in rows]


@router.get("/vehicle-downtime")
async def vehicle_downtime(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("select * from mart_vehicle_downtime"))
    rows = result.mappings().all()
    return [dict(r) for r in rows]


@router.get("/vehicle-fuel-efficiency")
async def vehicle_fuel_efficiency(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("select * from mart_vehicle_fuel_efficiency"))
    rows = result.mappings().all()
    return [dict(r) for r in rows]


@router.get("/customer-ltv")
async def customer_ltv(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("select * from mart_customer_ltv"))
    rows = result.mappings().all()
    return [dict(r) for r in rows]


@router.get("/calculations")
async def calculations():
    """Возвращает описание и формулы всех аналитических показателей."""
    return {
        name: {
            "description": meta["description"],
            "formula": meta["formula"],
        }
        for name, meta in CALCULATIONS.items()
    }
