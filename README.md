# Fleet Analytics Platform

Аналитическая платформа автопарка с эмуляцией интеграций **Битрикс24**, **UIS** и **1С**.

## Стек

- Python + FastAPI
- PostgreSQL 16
- Redis 7
- Metabase
- Docker Compose

## Запуск

```bash
docker compose up -d --build
```

- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Metabase: http://localhost:3000

## Эндпоинты MVP

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/health` | health-check |
| POST | `/sync/generate` | сгенерировать синтетические данные |
| GET | `/sync/state` | состояние синхронизации |
| POST | `/webhooks/bitrix24` | приём событий из CRM |
| POST | `/webhooks/uis` | приём событий телефонии |
| POST | `/webhooks/1c` | приём событий 1С |
| POST | `/analytics/recalc` | пересчитать аналитические витрины |
| GET | `/analytics/call-conversion` | витрина конверсии звонков |
| GET | `/analytics/vehicle-efficiency` | витрина эффективности автомобилей |
| GET | `/analytics/order-profitability` | витрина прибыльности заказов |

## Быстрый старт

1. Запустить стек: `docker compose up -d --build`
2. Сгенерировать данные: `curl -X POST http://localhost:8000/sync/generate`
3. Пересчитать витрины: `curl -X POST http://localhost:8000/analytics/recalc`
4. Открыть Metabase: http://localhost:3000 и подключиться к БД `fleet_analytics`
5. Проверить API: http://localhost:8000/docs

## Структура

```
fleet-analytics/
├── app/
│   ├── main.py
│   ├── models.py
│   ├── routers/
│   │   ├── analytics.py
│   │   ├── health.py
│   │   ├── sync.py
│   │   └── webhooks.py
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
└── README.md
```

## Сущности

- `crm_contacts` — контакты из CRM
- `crm_deals` — сделки
- `calls` — звонки из телефонии
- `vehicles` — автомобили
- `drivers` — водители
- `transport_orders` — заказы на перевозку
- `repairs` — ремонты
- `fuel_transactions` — заправки

## Аналитические витрины

- `mart_call_conversion` — конверсия звонков в сделки по месяцам
- `mart_vehicle_efficiency` — выручка, затраты и прибыль по автомобилям
- `mart_order_profitability` — прибыльность каждого заказа
