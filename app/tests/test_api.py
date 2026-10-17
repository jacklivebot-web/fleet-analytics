"""
Интеграционные тесты API.

Запускаются против реального поднятого контейнера app.
Проверяют основные сценарии: health, webhooks, синхронизацию,
аналитические витрины, mock-сервисы, scheduler и data-quality.
"""

import requests

BASE_URL = "http://localhost:8000"
SECRET_TOKEN = "demo-token-change-in-prod"


def test_health():
    """Проверяет, что API жив."""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_webhook_bitrix24():
    """Webhook из Битрикс24 с правильным токеном принимается."""
    payload = {"event": "ONCRMDEALUPDATE", "data": {"FIELDS": {"ID": "123"}}}
    response = requests.post(
        f"{BASE_URL}/webhooks/bitrix24",
        json=payload,
        headers={"X-Secret-Token": SECRET_TOKEN},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_webhook_uis():
    """Webhook из UIS с правильным токеном принимается."""
    payload = {"event": "call_finished", "call_id": "call-test", "phone": "+799****0000"}
    response = requests.post(
        f"{BASE_URL}/webhooks/uis",
        json=payload,
        headers={"X-Secret-Token": SECRET_TOKEN},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_webhook_1c():
    """Webhook из 1С с правильным токеном принимается."""
    payload = {"event": "order_updated", "order_id": "order-1"}
    response = requests.post(
        f"{BASE_URL}/webhooks/1c",
        json=payload,
        headers={"X-Secret-Token": SECRET_TOKEN},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_webhook_without_token_is_rejected():
    """Webhook без токена должен быть отклонён."""
    payload = {"event": "ONCRMDEALUPDATE"}
    response = requests.post(f"{BASE_URL}/webhooks/bitrix24", json=payload)
    assert response.status_code == 200
    assert response.json()["ok"] is False


def test_sync_state():
    """Эндпоинт /sync/state возвращает список состояний синхронизации."""
    response = requests.get(f"{BASE_URL}/sync/state")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_sync_generate_is_idempotent():
    """Повторный вызов /sync/generate без force возвращает те же данные."""
    first = requests.post(f"{BASE_URL}/sync/generate").json()
    second = requests.post(f"{BASE_URL}/sync/generate").json()
    assert first == second
    assert first["contacts"] == 50
    assert first["deals"] == 100
    assert first["calls"] == 500


def test_sync_generate_force():
    """Перегенерация через force=true возвращает ожидаемые объёмы."""
    response = requests.post(f"{BASE_URL}/sync/generate?force=true")
    assert response.status_code == 200
    data = response.json()
    assert data["contacts"] == 50


def test_analytics_recalc():
    """Пересчёт витрин завершается успешно."""
    response = requests.post(f"{BASE_URL}/analytics/recalc")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_analytics_vehicle_efficiency():
    """Витрина vehicle-efficiency содержит ожидаемые поля."""
    response = requests.get(f"{BASE_URL}/analytics/vehicle-efficiency")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    if data:
        assert "plate" in data[0]
        assert "profit" in data[0]


def test_analytics_call_conversion():
    """Витрина call-conversion содержит ожидаемые поля."""
    response = requests.get(f"{BASE_URL}/analytics/call-conversion")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "period" in data[0]
        assert "conversion_percent" in data[0]


def test_analytics_order_profitability():
    """Витрина order-profitability содержит ожидаемые поля."""
    response = requests.get(f"{BASE_URL}/analytics/order-profitability")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "order_id" in data[0]
        assert "margin_percent" in data[0]


def test_analytics_vehicle_downtime():
    """Витрина vehicle-downtime содержит ожидаемые поля."""
    response = requests.get(f"{BASE_URL}/analytics/vehicle-downtime")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "downtime_days" in data[0]


def test_analytics_vehicle_fuel_efficiency():
    """Витрина vehicle-fuel-efficiency содержит ожидаемые поля."""
    response = requests.get(f"{BASE_URL}/analytics/vehicle-fuel-efficiency")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "liters_per_100km" in data[0]


def test_analytics_customer_ltv():
    """Витрина customer-ltv содержит ожидаемые поля."""
    response = requests.get(f"{BASE_URL}/analytics/customer-ltv")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "ltv" in data[0]


def test_analytics_calculations():
    """Эндпоинт /analytics/calculations возвращает все формулы."""
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
    """Mock-эндпоинт сделок возвращает список."""
    response = requests.get(f"{BASE_URL}/mock/bitrix/deals")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "id" in data[0]


def test_mock_uis_calls():
    """Mock-эндпоинт звонков возвращает список."""
    response = requests.get(f"{BASE_URL}/mock/uis/calls")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "call_id" in data[0]


def test_mock_1c_vehicles():
    """Mock-эндпоинт автомобилей возвращает список."""
    response = requests.get(f"{BASE_URL}/mock/1c/vehicles")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "plate" in data[0]


def test_scheduler_all():
    """Scheduler запускает синхронизацию трёх источников."""
    response = requests.post(f"{BASE_URL}/scheduler/all")
    assert response.status_code == 200
    data = response.json()
    assert "scheduled" in data
    assert len(data["scheduled"]) == 3


def test_data_quality():
    """Data-quality возвращает сводку с ожидаемыми проверками."""
    response = requests.get(f"{BASE_URL}/data-quality/")
    assert response.status_code == 200
    data = response.json()
    assert "overall" in data
    assert "checks" in data
    assert isinstance(data["checks"], dict)
    assert "duplicate_contacts_by_phone" in data["checks"]
    assert "won_deals_without_order" in data["checks"]
