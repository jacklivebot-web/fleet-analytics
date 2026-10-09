# Fleet Analytics Platform

Аналитическая платформа автопарка с эмуляцией интеграций **Битрикс24**, **UIS** и **1С**.

## Стек

- Python + FastAPI
- PostgreSQL 16
- Redis 7
- Metabase
- Docker Compose
- Alembic

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
| POST | `/sync/generate` | сгенерировать синтетические данные (или вернуть текущие) |
| GET | `/sync/state` | состояние синхронизации |
| POST | `/webhooks/bitrix24` | приём событий из CRM |
| POST | `/webhooks/uis` | приём событий телефонии |
| POST | `/webhooks/1c` | приём событий 1С |
| POST | `/analytics/recalc` | пересчитать аналитические витрины |
| GET | `/analytics/call-conversion` | витрина конверсии звонков |
| GET | `/analytics/vehicle-efficiency` | витрина эффективности автомобилей |
| GET | `/analytics/order-profitability` | витрина прибыльности заказов |
| GET | `/mock/bitrix/deals` | mock данные сделок |
| GET | `/mock/bitrix/contacts` | mock данные контактов |
| GET | `/mock/uis/calls` | mock данные звонков |
| GET | `/mock/1c/vehicles` | mock данные автомобилей |
| GET | `/mock/1c/orders` | mock данные заказов |
| POST | `/scheduler/all` | запуск синхронизации всех источников |

## Быстрый старт

1. Запустить стек: `docker compose up -d --build`
2. Применить миграции: `cd app && docker compose exec app alembic upgrade head`
3. Сгенерировать данные: `curl -X POST http://localhost:8000/sync/generate`
4. Пересчитать витрины: `curl -X POST http://localhost:8000/analytics/recalc`
5. Настроить Metabase: `cd app && docker compose exec app python scripts/setup_metabase.py`
6. Открыть публичный дашборд (URL будет в выводе скрипта)

## Миграции Alembic

```bash
cd app
docker compose exec app alembic upgrade head
docker compose exec app alembic revision --autogenerate -m "описание"
```

## Настройка Metabase

```bash
cd app
docker compose exec app python scripts/setup_metabase.py
```

Логин: `admin@fleet.local`  
Пароль: `FleetAnalytics123!`

## Тесты

```bash
cd app
docker compose exec app python -m pytest tests/test_api.py -v
```

## Структура

```
fleet-analytics/
├── app/
│   ├── main.py
│   ├── models.py
│   ├── routers/
│   │   ├── analytics.py
│   │   ├── health.py
│   │   ├── mock_services.py
│   │   ├── scheduler.py
│   │   ├── sync.py
│   │   └── webhooks.py
│   ├── scripts/
│   │   └── setup_metabase.py
│   ├── tests/
│   │   └── test_api.py
│   ├── migrations/
│   │   ├── env.py
│   │   └── versions/
│   ├── Dockerfile
│   ├── alembic.ini
│   └── requirements.txt
├── db/
│   └── init-metabase-db.sql
├── docker-compose.yml
├── README.md
├── CASES.md
└── PORTFOLIO.md
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

## Документы

- `CASES.md` — разбор задач из вакансии
- `PORTFOLIO.md` — краткое кейс-стадио для портфолио

