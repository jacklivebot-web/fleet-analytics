import requests
import time

BASE = "http://localhost:3000"
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
    cards = []
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
    ]

    for q in questions:
        payload = {
            "name": q["name"],
            "collection_id": collection_id,
            "dataset_query": {
                "database": 2,
                "type": "native",
                "native": {"query": q["sql"]},
            },
            "display": q["display"],
            "visualization_settings": q["viz"],
        }
        r = requests.post(f"{BASE}/api/card", headers=headers, json=payload)
        if r.status_code == 200:
            cards.append(r.json()["id"])

    # Dashboard
    r = requests.post(
        f"{BASE}/api/dashboard",
        headers=headers,
        json={"name": "Fleet Analytics MVP", "collection_id": collection_id, "parameters": []},
    )
    dashboard_id = r.json()["id"]

    # Add cards
    dashboard_cards = []
    positions = [(0, 0, 12, 8), (0, 12, 12, 8), (8, 0, 24, 10)]
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

    # Public link
    r = requests.post(f"{BASE}/api/dashboard/{dashboard_id}/public_link", headers=headers)
    public_uuid = r.json().get("uuid")

    print(f"Dashboard created: {BASE}/public/dashboard/{public_uuid}")
    return dashboard_id


if __name__ == "__main__":
    token = setup_metabase()
    if token:
        create_dashboard(token)
