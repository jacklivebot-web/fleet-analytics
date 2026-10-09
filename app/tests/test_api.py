import requests

BASE_URL = "http://localhost:8000"
SECRET_TOKEN = "demo-token-change-in-prod"


def test_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_webhook_bitrix24():
    payload = {"event": "ONCRMDEALUPDATE", "data": {"FIELDS": {"ID": "123"}}}
    response = requests.post(
        f"{BASE_URL}/webhooks/bitrix24",
        json=payload,
        headers={"X-Secret-Token": SECRET_TOKEN},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_webhook_uis():
    payload = {"event": "call_finished", "call_id": "call-test", "phone": "+79990000000"}
    response = requests.post(
        f"{BASE_URL}/webhooks/uis",
        json=payload,
        headers={"X-Secret-Token": SECRET_TOKEN},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_webhook_1c():
    payload = {"event": "order_updated", "order_id": "order-1"}
    response = requests.post(
        f"{BASE_URL}/webhooks/1c",
        json=payload,
        headers={"X-Secret-Token": SECRET_TOKEN},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_webhook_without_token_is_rejected():
    payload = {"event": "ONCRMDEALUPDATE"}
    response = requests.post(f"{BASE_URL}/webhooks/bitrix24", json=payload)
    assert response.status_code == 200
    assert response.json()["ok"] is False


def test_sync_state():
    response = requests.get(f"{BASE_URL}/sync/state")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_sync_generate_is_idempotent():
    first = requests.post(f"{BASE_URL}/sync/generate").json()
    second = requests.post(f"{BASE_URL}/sync/generate").json()
    assert first == second
    assert first["contacts"] == 50
    assert first["deals"] == 100
    assert first["calls"] == 500


def test_sync_generate_force():
    response = requests.post(f"{BASE_URL}/sync/generate?force=true")
    assert response.status_code == 200
    data = response.json()
    assert data["contacts"] == 50


def test_analytics_recalc():
    response = requests.post(f"{BASE_URL}/analytics/recalc")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_analytics_vehicle_efficiency():
    response = requests.get(f"{BASE_URL}/analytics/vehicle-efficiency")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    if data:
        assert "plate" in data[0]
        assert "profit" in data[0]


def test_analytics_call_conversion():
    response = requests.get(f"{BASE_URL}/analytics/call-conversion")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "period" in data[0]
        assert "conversion_percent" in data[0]


def test_analytics_order_profitability():
    response = requests.get(f"{BASE_URL}/analytics/order-profitability")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "order_id" in data[0]
        assert "margin_percent" in data[0]


def test_analytics_vehicle_downtime():
    response = requests.get(f"{BASE_URL}/analytics/vehicle-downtime")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "downtime_days" in data[0]


def test_analytics_vehicle_fuel_efficiency():
    response = requests.get(f"{BASE_URL}/analytics/vehicle-fuel-efficiency")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "liters_per_100km" in data[0]


def test_analytics_customer_ltv():
    response = requests.get(f"{BASE_URL}/analytics/customer-ltv")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "ltv" in data[0]


def test_analytics_calculations():
    response = requests.get(f"{BASE_URL}/analytics/calculations")
    assert response.status_code == 200
    data = response.json()
    assert "call_conversion" in data
    assert "vehicle_efficiency" in data
    assert "order_profitability" in data
    assert "vehicle_downtime" in data
    assert "vehicle_fuel_efficiency" in data
    assert "customer_ltv" in data


def test_mock_bitrix_deals():
    response = requests.get(f"{BASE_URL}/mock/bitrix/deals")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "id" in data[0]


def test_mock_uis_calls():
    response = requests.get(f"{BASE_URL}/mock/uis/calls")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "call_id" in data[0]


def test_mock_1c_vehicles():
    response = requests.get(f"{BASE_URL}/mock/1c/vehicles")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "plate" in data[0]


def test_scheduler_all():
    response = requests.post(f"{BASE_URL}/scheduler/all")
    assert response.status_code == 200
    data = response.json()
    assert "scheduled" in data
    assert len(data["scheduled"]) == 3
