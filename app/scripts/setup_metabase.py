import requests
import time
import os

BASE = os.getenv("METABASE_BASE_URL", "http://fleet_metabase:3000")
EMAIL = "admin@fleet.local"
PASSWORD = "FleetAnalytics123!"


def setup_metabase():
    props = requests.get(f"{BASE}/api/session/properties").json()
    token = props.get("setup-token")

    if not token:
        print("Metabase already set up or no setup token")
        return login()

    payload = {
        "token": token,
        "user": {
            "first_name": "Fleet",
            "last_name": "Admin",
            "email": EMAIL,
            "password": PASSWORD,
            "password_confirm": PASSWORD,
        },
        "prefs": {"site_name": "Fleet Analytics", "site_locale": "en"},
        "database": {
            "engine": "postgres",
            "name": "Fleet Analytics DB",
            "details": {
                "host": "db",
                "port": 5432,
                "dbname": "fleet_analytics",
                "user": "fleet",
                "password": "fleet",
                "schema-filters-type": "all",
                "ssl": False,
                "tunnel-enabled": False,
            },
            "auto_run_queries": True,
            "is_full_sync": True,
            "is_on_demand": False,
        },
        "allow_tracking": False,
    }

    r = requests.post(f"{BASE}/api/setup", json=payload)
    if r.status_code == 200:
        print("Metabase setup completed")
    else:
        print("Setup failed:", r.status_code, r.text[:300])

    return login()


def login():
    r = requests.post(f"{BASE}/api/session", json={"username": EMAIL, "password": PASSWORD})
    if r.status_code != 200:
        print("Login failed:", r.status_code, r.text[:300])
        return None
    return r.json()["id"]


def create_dashboard(token):
    headers = {"X-Metabase-Session": token}

    # Collection
    r = requests.post(f"{BASE}/api/collection", headers=headers, json={"name": "Fleet Analytics", "color": "#509EE3"})
    collection_id = r.json().get("id", 5)

    # Cards
    questions = [
        {
            "name": "Прибыльность автомобилей",
            "sql": "select plate, model, profit from mart_vehicle_efficiency order by profit desc limit 10",
            "display": "bar",
            "viz": {"graph.dimensions": ["plate"], "graph.metrics": ["profit"]},
        },
        {
            "name": "Конверсия звонков по месяцам",
            "sql": "select period, calls, calls_with_deal, conversion_percent from mart_call_conversion order by period",
            "display": "line",
            "viz": {"graph.dimensions": ["period"], "graph.metrics": ["conversion_percent"]},
        },
        {
            "name": "Прибыльность заказов",
            "sql": "select order_id, route_name, revenue, cost, profit, margin_percent from mart_order_profitability order by profit desc limit 20",
            "display": "table",
            "viz": {},
        },
        {
            "name": "Воронка продаж",
            "sql": """
select 'Заявки' as stage, count(distinct d.id) as value from crm_deals d
union all
select 'Со звонком', count(distinct c.deal_id) from calls c where c.status = 'answered'
union all
select 'Выданы', count(distinct o.deal_id) from transport_orders o where o.status = 'completed'
            """,
            "display": "funnel",
            "viz": {},
        },
        {
            "name": "Загрузка автопарка по статусам",
            "sql": "select status, count(*) as count from vehicles group by 1",
            "display": "pie",
            "viz": {},
        },
        {
            "name": "Средняя длительность звонка по операторам",
            "sql": "select employee_id, avg(duration_sec) as avg_duration, count(*) as calls from calls group by 1 order by 2 desc",
            "display": "bar",
            "viz": {"graph.dimensions": ["employee_id"], "graph.metrics": ["avg_duration"]},
        },
        {
            "name": "Пропущенные звонки по месяцам",
            "sql": "select date_trunc('month', started_at)::text as month, count(*) from calls where status='missed' group by 1 order by 1",
            "display": "line",
            "viz": {"graph.dimensions": ["month"], "graph.metrics": ["count"]},
        },
        {
            "name": "Доходность по моделям",
            "sql": "select v.model, sum(o.revenue) as revenue, sum(o.cost) as cost, sum(o.revenue - o.cost) as profit from vehicles v left join transport_orders o on o.vehicle_id=v.id group by 1 order by profit desc",
            "display": "bar",
            "viz": {"graph.dimensions": ["model"], "graph.metrics": ["profit"]},
        },
    ]

    # Find or create database connection
    databases = requests.get(f"{BASE}/api/database", headers=headers).json().get("data", [])
    db_conn = next((d for d in databases if d["name"] == "Fleet Analytics DB"), None)
    if db_conn:
        database_id = db_conn["id"]
    else:
        payload = {
            "engine": "postgres",
            "name": "Fleet Analytics DB",
            "details": {
                "host": "db",
                "port": 5432,
                "dbname": "fleet_analytics",
                "user": "fleet",
                "password": "fleet",
                "schema-filters-type": "all",
                "ssl": False,
                "tunnel-enabled": False,
            },
            "auto_run_queries": True,
            "is_full_sync": True,
            "is_on_demand": False,
        }
        r = requests.post(f"{BASE}/api/database", headers=headers, json=payload)
        database_id = r.json()["id"]

    # Sync schema
    requests.post(f"{BASE}/api/database/{database_id}/sync", headers=headers)
    requests.post(f"{BASE}/api/database/{database_id}/rescan_values", headers=headers)
    time.sleep(2)

    cards = []
    for q in questions:
        payload = {
            "name": q["name"],
            "collection_id": collection_id,
            "dataset_query": {
                "database": database_id,
                "type": "native",
                "native": {"query": q["sql"]},
            },
            "display": q["display"],
            "visualization_settings": q["viz"],
        }
        r = requests.post(f"{BASE}/api/card", headers=headers, json=payload)
        if r.status_code == 200:
            cards.append(r.json()["id"])
        else:
            print(f"Failed to create card {q['name']}:", r.status_code, r.text[:200])

    # Dashboard
    r = requests.post(
        f"{BASE}/api/dashboard",
        headers=headers,
        json={"name": "Fleet Analytics MVP", "collection_id": collection_id, "parameters": []},
    )
    dashboard_id = r.json()["id"]

    # Add cards
    dashboard_cards = []
    positions = [
        (0, 0, 12, 8),    # Прибыльность автомобилей
        (0, 12, 12, 8),   # Конверсия звонков
        (8, 0, 24, 10),   # Прибыльность заказов
        (18, 0, 12, 8),   # Воронка продаж
        (18, 12, 12, 8),  # Загрузка по статусам
        (26, 0, 12, 8),   # Длительность звонков
        (26, 12, 12, 8),  # Пропущенные звонки
        (34, 0, 12, 8),   # Доходность по моделям
    ]
    for card_id, (row, col, sx, sy) in zip(cards, positions):
        dashboard_cards.append(
            {
                "id": card_id,
                "card_id": card_id,
                "row": row,
                "col": col,
                "size_x": sx,
                "size_y": sy,
                "series": [],
                "parameter_mappings": [],
            }
        )

    r = requests.put(
        f"{BASE}/api/dashboard/{dashboard_id}/cards",
        headers=headers,
        json={"cards": dashboard_cards},
    )
    if r.status_code != 200:
        print("Dashboard cards update failed:", r.status_code, r.text[:300])

    # Public link
    r = requests.post(f"{BASE}/api/dashboard/{dashboard_id}/public_link", headers=headers)
    public_uuid = r.json().get("uuid")

    print(f"Dashboard created: {BASE}/public/dashboard/{public_uuid}")
    return dashboard_id


if __name__ == "__main__":
    token = setup_metabase()
    if token:
        create_dashboard(token)
