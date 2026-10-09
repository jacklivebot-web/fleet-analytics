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
