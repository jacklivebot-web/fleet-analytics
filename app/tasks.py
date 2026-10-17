"""
Celery-задачи.

Запускаются Celery Beat ежедневно и имитируют полный цикл:
синхронизация из трёх источников + пересчёт аналитических витрин.

В продакшене здесь будут реальные вызовы API внешних систем.
"""

import os
import requests
from celery import Celery

app = Celery("fleet_analytics")
app.config_from_object("celeryconfig")

BASE_URL = os.getenv("FLEET_API_URL", "http://app:8000")
SECRET = os.getenv("SECRET_TOKEN", "demo-token-change-in-prod")
HEADERS = {"X-Secret-Token": SECRET}


@app.task
def sync_bitrix24():
    """Фоновая синхронизация с Битрикс24."""
    r = requests.post(f"{BASE_URL}/scheduler/bitrix24", headers=HEADERS, timeout=60)
    return {"source": "bitrix24", "status": r.status_code, "ok": r.json().get("ok")}


@app.task
def sync_uis():
    """Фоновая синхронизация с UIS."""
    r = requests.post(f"{BASE_URL}/scheduler/uis", headers=HEADERS, timeout=60)
    return {"source": "uis", "status": r.status_code, "ok": r.json().get("ok")}


@app.task
def sync_1c():
    """Фоновая синхронизация с 1С."""
    r = requests.post(f"{BASE_URL}/scheduler/1c", headers=HEADERS, timeout=60)
    return {"source": "1c", "status": r.status_code, "ok": r.json().get("ok")}


@app.task
def recalc_marts():
    """Фоновый пересчёт аналитических витрин."""
    r = requests.post(f"{BASE_URL}/analytics/recalc", timeout=120)
    return {"task": "recalc", "status": r.status_code, "ok": r.json().get("ok")}
