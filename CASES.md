# Fleet Analytics Platform — Кейсы для вакансии

> Проект от Jack. Решает задачи из вакансии аналитика данных / BI-аналитика в компании по аренде/выдаче автомобилей для такси.

## 1. Сборка и сопоставление данных из источников

**Что сделано:**

- FastAPI-приложение принимает webhook-события из **Битрикс24**, **UIS**, **1С**.
- Mock-эндпоинты `/mock/bitrix/*`, `/mock/uis/*`, `/mock/1c/*` имитируют структуру реальных данных.
- Все события сохраняются в `raw_events` для аудита и повторной обработки.
- Фоновая синхронизация запускается через Celery Beat.

**Как связаны данные:**

- CRM-контакт ↔ звонок по `phone_normalized`.
- Сделка ↔ заказ по `deal_id`.
- Автомобиль ↔ заказ по `vehicle_id`.

## 2. Проверка корректности показателей

**Инструменты:**

- `GET /sync/state` — время последней успешной синхронизации каждого источника.
- `POST /scheduler/all` — ручной запуск синхронизации.
- `GET /data-quality/` — 13 автоматических проверок качества данных.
- `app/tests/test_api.py` — 21 тест, покрывающий health, webhooks, генерацию данных, пересчёт витрин, data-quality.

**Пример поиска дублей:**

```sql
select phone_normalized, count(*)
from crm_contacts
group by 1
having count(*) > 1;
```

## 3. Воронка продаж

**Реализация:**

- Витрина и SQL-запрос в Metabase: заявки → звонки → выдачи.
- Эндпоинт `/analytics/call-conversion`.
- Дашборд включает воронку, конверсию по месяцам, пропущенные звонки и конверсию по этапам.

## 4. Путь клиента

Полный путь клиента покрыт данными:

- Заявка: `crm_deals`
- Звонок: `calls` (связь через `deal_id` и `phone_normalized`)
- Выдача: `transport_orders` со статусом `completed`

## 5. Показатели парка

**По автомобилям:**

- `mart_vehicle_efficiency`: выручка, затраты, прибыль, количество заказов.
- `mart_vehicle_downtime`: дни в ремонте и затраты.
- `mart_vehicle_fuel_efficiency`: расход топлива.
- Статусы автомобилей: `active`, `repair`, `idle`.

**По городам и моделям:**

- Дашборд включает доходность по моделям, загрузку по статусам, расход топлива, затраты на ремонт.

## 6. Доходность автомобиля

**Формула:**

```
profit = revenue - cost
margin_percent = profit / revenue * 100
```

**Витрины:** `mart_order_profitability` + `mart_vehicle_efficiency`.

## 7. Анализ звонков с помощью ИИ

**Статус:** в MVP реализована структура и тестовые данные.

**Следующий шаг:**

- Добавить поля `transcript`, `ai_reason_refusal`, `ai_satisfaction_score` в таблицу `calls`.
- Интегрировать локальную LLM (Ollama Cloud) для транскрибации и классификации.
- Создать витрину `mart_call_ai_summary`.

## 8. Автоматизация регулярных выгрузок

**Сделано:**

- `POST /scheduler/all` — ручной запуск синхронизации всех источников.
- Celery Beat запускает `sync_bitrix24`, `sync_uis`, `sync_1c`, `recalc_marts` ежедневно.

**Задачи:**

- `tasks.sync_bitrix24`
- `tasks.sync_uis`
- `tasks.sync_1c`
- `tasks.recalc_marts`

## Как запустить для демонстрации

```bash
cd ~/projects/fleet-analytics
docker compose up -d --build
cd app
docker compose exec app alembic upgrade head
docker compose exec app python scripts/setup_metabase.py
```

API: http://localhost:8000/docs

## Автор

Jack — аналитик данных / BI-аналитик.
