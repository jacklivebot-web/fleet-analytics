import requests

BASE_URL = "http://localhost:8000"

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_webhook_bitrix24():
    payload = {"event": "ONCRMDEALUPDATE", "data": {"FIELDS": {"ID": "123"}}}
    response = requests.post(f"{BASE_URL}/webhooks/bitrix24", json=payload, headers={"X-Secret-Token": "demo-token-change-in-prod"})
    assert response.status_code == 200
    assert response.json()["ok"] is True

def test_webhook_uis():
    payload = {"event": "call_finished", "call_id": "call-test", "phone": "+79990000000"}
    response = requests.post(f"{BASE_URL}/webhooks/uis", json=payload, headers={"X-Secret-Token": "demo-token-change-in-prod"})
    assert response.status_code == 200
    assert response.json()["ok"] is True

def test_webhook_1c():
    payload = {"event": "order_updated", "order_id": "order-1"}
    response = requests.post(f"{BASE_URL}/webhooks/1c", json=payload, headers={"X-Secret-Token": "demo-token-change-in-prod"})
    assert response.status_code == 200
    assert response.json()["ok"] is True

def test_sync_state():
    response = requests.get(f"{BASE_URL}/sync/state")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

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
