# Fleet Analytics Platform

Личный pet-проект, который я сделал как **портфолио-кейс** на позицию аналитика данных / BI-инженера / инженера данных.

Суть: собрать данные из трёх разных систем компании, которая занимается автопарком — **Битрикс24** (CRM), **UIS** (телефония) и **1С** (учёт ТС и заказов) — и превратить их в прозрачные, проверяемые аналитические показатели. Без «магии», без Excel-табличек на коленке, без доверия к цифре «потому что так сказал отдел продаж».

## Зачем я это делал

Когда я смотрю на вакансии аналитика, там обычно хотят:

- уметь вытаскивать данные из разных источников;
- строить хранилище / витрины;
- считать unit-экономику, конверсии, эффективность;
- визуализировать в BI;
- проверять качество данных;
- автоматизировать рутину.

Я решил не рассказывать об этом на словах, а сделать законченный минимальный продукт, который можно поднять одной командой и показать интервьюеру.

## Что внутри

- **FastAPI + SQLAlchemy asyncpg** — API и ETL-витрины.
- **PostgreSQL 16** — единое хранилище.
- **Redis 7** — брокер для фоновых задач.
- **Metabase** — BI-дашборды.
- **Docker Compose** — весь стек поднимается локально.
- **Alembic** — версионирование схемы БД.
- **Celery Beat** — ежедневная синхронизация и пересчёт витрин.

## Запуск

```bash
cd ~/projects/fleet-analytics
docker compose up -d --build
```

После старта:

- API: http://localhost:8000
- Документация: http://localhost:8000/docs
- Metabase: http://localhost:3000

## Быстрый старт

```bash
# 1. Поднять стек
cd ~/projects/fleet-analytics
docker compose up -d --build

# 2. Применить миграции Alembic
cd app
docker compose exec app alembic upgrade head

# 3. Сгенерировать синтетические данные
curl -X POST http://localhost:8000/sync/generate

# 4. Пересчитать аналитические витрины
curl -X POST http://localhost:8000/analytics/recalc

# 5. Настроить Metabase (создаст админа, БД, дашборд)
docker compose exec app python scripts/setup_metabase.py
```

Публичная ссылка на дашборд появится в консоли. Можно сразу скидывать HR или интервьюеру.

## Эндпоинты MVP

| Метод | URL | Что делает |
|-------|-----|------------|
| GET | `/health` | Проверка, что API жив |
| POST | `/sync/generate` | Генерация синтетических данных (идемпотентна) |
| POST | `/sync/generate?force=true` | Принудительная перегенерация |
| GET | `/sync/state` | Состояние синхронизации по источникам |
| POST | `/webhooks/bitrix24` | Webhook из Битрикс24 |
| POST | `/webhooks/uis` | Webhook из UIS |
| POST | `/webhooks/1c` | Webhook из 1С |
| POST | `/analytics/recalc` | Пересчитать все витрины |
| GET | `/analytics/calculations` | Открытые формулы расчёта показателей |
| GET | `/analytics/call-conversion` | Конверсия звонков в сделки |
| GET | `/analytics/vehicle-efficiency` | Эффективность автомобилей |
| GET | `/analytics/order-profitability` | Прибыльность заказов |
| GET | `/analytics/vehicle-downtime` | Простой и ремонты ТС |
| GET | `/analytics/vehicle-fuel-efficiency` | Расход топлива |
| GET | `/analytics/customer-ltv` | LTV клиентов |
| GET | `/mock/bitrix/deals` | Mock-сделки Битрикс24 |
| GET | `/mock/bitrix/contacts` | Mock-контакты Битрикс24 |
| GET | `/mock/uis/calls` | Mock-звонки UIS |
| GET | `/mock/1c/vehicles` | Mock-автомобили 1С |
| GET | `/mock/1c/orders` | Mock-заказы 1С |
| POST | `/scheduler/all` | Ручной запуск синхронизации всех источников |
| GET | `/data-quality/` | 13 проверок качества данных |

## Структура репозитория

```
fleet-analytics/
├── app/
│   ├── main.py                      # точка входа FastAPI
│   ├── models.py                    # SQLAlchemy модели, engine, сессии
│   ├── celeryconfig.py              # настройки Celery
│   ├── tasks.py                     # фоновые задачи
│   ├── routers/
│   │   ├── analytics.py             # витрины и пересчёт
│   │   ├── data_quality.py          # проверки качества данных
│   │   ├── health.py                # health-check
│   │   ├── mock_services.py         # mock-источники данных
│   │   ├── scheduler.py             # ручной запуск синхронизации
│   │   ├── sync.py                  # генератор синтетических данных
│   │   └── webhooks.py              # webhook-эндпоинты
│   ├── scripts/
│   │   └── setup_metabase.py        # автоматическая настройка Metabase
│   ├── tests/
│   │   └── test_api.py              # 21 интеграционный тест
│   ├── migrations/                  # Alembic миграции
│   ├── Dockerfile
│   ├── alembic.ini
│   └── requirements.txt
├── db/
│   └── init-metabase-db.sql         # инициализация отдельной БД для Metabase
├── docker-compose.yml
├── README.md                        # этот файл
├── CASES.md                         # разбор задач вакансии
├── PORTFOLIO.md                     # кейс-стадио для портфолио
├── DATA_DICTIONARY.md               # описание таблиц и полей
└── .gitignore
```

## Ключевые сущности

- `crm_contacts` — контакты из CRM.
- `crm_deals` — сделки и этапы воронки.
- `calls` — звонки из телефонии.
- `vehicles` — автомобили из 1С.
- `drivers` — водители.
- `transport_orders` — заказы на перевозку / выдачу авто.
- `repairs` — ремонты ТС.
- `fuel_transactions` — заправки топлива.

## Аналитические витрины

- `mart_call_conversion` — конверсия звонков в сделки по месяцам.
- `mart_vehicle_efficiency` — выручка, затраты и прибыль по автомобилям.
- `mart_order_profitability` — прибыльность каждого заказа.
- `mart_vehicle_downtime` — дни простоя и затраты на ремонты.
- `mart_vehicle_fuel_efficiency` — расход топлива на 100 км.
- `mart_customer_ltv` — пожизненная ценность клиента (LTV).

Каждая витрина пересчитывается целиком через `POST /analytics/recalc`.

## Проверка качества данных

Эндпоинт `GET /data-quality/` возвращает сводку: общий статус + 13 конкретных проверок. Примеры:

- дубли контактов по телефону;
- звонки без привязки к сделке или контакту;
- заказы без ТС или водителя;
- отрицательная выручка/затраты;
- аномальный расход топлива;
- выигранные сделки без выданного автомобиля;
- ремонты с отрицательной длительностью.

```bash
curl http://localhost:8000/data-quality/
```

## Открытые формулы

Все показатели и их формулы можно достать через API, чтобы никто не спрашивал «а откуда цифра»:

```bash
curl http://localhost:8000/analytics/calculations
```

Ключевые расчёты:

- **Конверсия звонков** = `calls_with_deal / calls * 100` (сделка связана, если `deal_id is not null`).
- **Прибыль автомобиля** = `sum(revenue) - sum(cost)` по всем заказам ТС.
- **Прибыль заказа** = `revenue - cost`.
- **Маржа заказа** = `(revenue - cost) / revenue * 100`.
- **Простой** = `sum(ended_at - started_at)` по ремонтам + дополнительный непрерывный простой.
- **Расход топлива** = `liters / distance_km * 100`.
- **LTV клиента** = `sum(revenue) - sum(cost)` по всем заказам клиента.

## Миграции

```bash
cd app
docker compose exec app alembic upgrade head
```

При изменении моделей:

```bash
cd app
docker compose exec app alembic revision --autogenerate -m "описание изменений"
```

## Metabase

Настройка автоматическая:

```bash
cd app
docker compose exec app python scripts/setup_metabase.py
```

- Логин: `admin@fleet.local`
- Пароль: `FleetAnalytics123!`

Скрипт создаёт подключение к БД Fleet Analytics, коллекцию, 21 карточку и дашборд `Fleet Analytics MVP` с публичной ссылкой.

## Тесты

Тесты идут против реально поднятого контейнера через `requests`:

```bash
cd app
docker compose exec app python -m pytest tests/test_api.py -v
```

21 тест покрывает: health, webhook-аутентификацию, генерацию данных, витрины, mock-сервисы, scheduler и data-quality.

## Документы

- `CASES.md` — разбор задач из вакансии, которые закрывает проект.
- `PORTFOLIO.md` — короткое кейс-стадио, которое можно вставить в портфолио.
- `DATA_DICTIONARY.md` — полное описание таблиц, полей и связей БД.

## Автор

Jack — аналитик данных / BI-аналитик. Проект делал для себя, чтобы показать, как я подхожу к данным: от источников до дашборда.
