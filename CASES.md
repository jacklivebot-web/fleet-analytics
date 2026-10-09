# Fleet Analytics Platform — Кейсы для вакансии

> Проект решает задачи из вакансии аналитика данных / BI-аналитика в компании по аренде автомобилей для такси.

## 1. Сборка и сопоставление данных из источников

**Что сделано:**
- FastAPI приложение принимает webhook-события из **Битрикс24**, **UIS**, **1С**.
- Mock-эндпоинты `/mock/bitrix/*`, `/mock/uis/*`, `/mock/1c/*` имитируют структуру реальных данных.
- Все события сохраняются в `raw_events` для аудита.

**Как связаны данные:**
- CRM-контакт ↔ звонок по `phone_normalized`.
- Сделка ↔ заказ по `deal_id`.
- Автомобиль ↔ заказ по `vehicle_id`.

## 2. Проверка корректности показателей

**Инструменты:**
- `GET /sync/state` — время последней успешной синхронизации каждого источника.
- `POST /scheduler/all` — ручной запуск синхронизации.
- Тесты `app/tests/test_api.py` проверяют health, webhooks, генерацию данных, пересчёт витрин.

**Пример поиска дублей:**
```sql
select phone_normalized, count(*)
from crm_contacts
group by 1
having count(*) > 1;
```

## 3. Воронка продаж

**Реализация:**
- Витрина: SQL-запрос в Metabase и роутер `/analytics/call-conversion`.
- Этапы: `Заявки` → `Со звонком` → `Выданы`.
- Дашборд: воронка, конверсия по месяцам, пропущенные звонки.

**Публичный дашборд:** http://localhost:3000/public/dashboard/8403a20a-d24e-45f0-85b8-b5aef11ecd30

## 4. Путь клиента

Данные покрывают полный путь:
- Заявка: `crm_deals`
- Звонок: `calls` (связь через `deal_id` и `phone_normalized`)
- Выдача: `transport_orders` со статусом `completed`

## 5. Показатели парка

**По автомобилям:**
- `mart_vehicle_efficiency`: выручка, затраты, прибыль, количество заказов.
- Статусы автомобилей: `active`, `repair`, `idle`.

**По городам и моделям:**
- Дашборд включает доходность по моделям и загрузку по статусам.

## 6. Доходность автомобиля

**Формула:**
```
profit = revenue - cost
margin_percent = profit / revenue * 100
```

**Витрина:** `mart_order_profitability` + `mart_vehicle_efficiency`.

## 7. Анализ звонков с помощью ИИ

**Статус:** в MVP реализована структура и тестовые данные.

**Следующий шаг:**
- Добавить поля `transcript`, `ai_reason_refusal`, `ai_satisfaction_score` в таблицу `calls`.
- Интегрировать локальную LLM (Ollama) или API для транскрибации и классификации.
- Создать витрину `mart_call_ai_summary`.

## 8. Автоматизация регулярных выгрузок

**Сделано:**
- `POST /scheduler/all` — ручной запуск синхронизации всех источников.

**Следующий шаг:**
- Добавить Celery Beat или cron-контейнер для ежедневного запуска:
  - `sync/bitrix24`
  - `sync/uis`
  - `sync/1c`
  - `analytics/recalc`

## Скриншоты

Открыть дашборд локально: http://localhost:3000/public/dashboard/801cf3fa-dcfd-4294-ab77-63aca19ea6f6

## Как запустить для демонстрации

```bash
cd ~/projects/fleet-analytics
docker compose up -d --build
cd app
docker compose exec app alembic upgrade head
docker compose exec app python scripts/setup_metabase.py
```

API: http://localhost:8000/docs  
Dashboard: http://localhost:3000/public/dashboard/801cf3fa-dcfd-4294-ab77-63aca19ea6f6
