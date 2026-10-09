# Data Dictionary — Fleet Analytics Platform

## Справочники и сырые события

### `sync_state`
Состояние синхронизации с внешними системами.

| Поле | Тип | Описание |
|------|-----|----------|
| id | serial PK | Идентификатор |
| source | varchar | Источник: `bitrix24`, `uis`, `1c` |
| last_success_at | timestamptz | Время последней успешной синхронизации |
| updated_at | timestamptz | Автообновление |

### `raw_events`
Все входящие события из webhook-ов.

| Поле | Тип | Описание |
|------|-----|----------|
| id | bigint PK | Идентификатор |
| source | varchar | Источник события |
| event_type | varchar | Тип события |
| payload | json | Тело события |
| created_at | timestamptz | Время получения |

## CRM

### `crm_contacts`
Контакты из Битрикс24.

| Поле | Тип | Описание |
|------|-----|----------|
| id | bigint PK | Идентификатор |
| bitrix_id | bigint | ID контакта в Битрикс24 |
| name | varchar | Имя |
| phone_normalized | varchar | Нормализованный телефон (11 цифр, начинается с 7) |
| email | varchar | Email |
| source_updated_at | timestamptz | Время обновления в источнике |
| raw_data | json | Сырые данные |

### `crm_deals`
Сделки из Битрикс24.

| Поле | Тип | Описание |
|------|-----|----------|
| id | bigint PK | Идентификатор |
| bitrix_id | bigint | ID сделки в Битрикс24 |
| title | varchar | Название |
| stage_id | varchar | Стадия: `new`, `in_progress`, `won`, `lost` |
| pipeline_id | varchar | Воронка |
| amount | numeric(15,2) | Сумма сделки |
| responsible_id | bigint | Ответственный |
| contact_id | bigint FK | Связь с `crm_contacts` |
| company_id | bigint | ID компании |
| created_at | timestamptz | Дата создания |
| closed_at | timestamptz | Дата закрытия |
| raw_data | json | Сырые данные |

## Телефония

### `calls`
Звонки из UIS.

| Поле | Тип | Описание |
|------|-----|----------|
| id | bigint PK | Идентификатор |
| provider | varchar | Провайдер (`uis`) |
| provider_call_id | varchar | ID звонка в провайдере |
| bitrix_activity_id | bigint | ID дела в Битрикс24 |
| direction | varchar | Направление: `inbound`, `outbound` |
| phone_normalized | varchar | Нормализованный номер |
| employee_id | bigint | Оператор |
| contact_id | bigint FK | Связь с контактом |
| deal_id | bigint FK | Связь со сделкой |
| started_at | timestamptz | Начало звонка |
| answered_at | timestamptz | Ответ |
| ended_at | timestamptz | Завершение |
| duration_sec | int | Длительность в секундах |
| wait_duration_sec | int | Время ожидания |
| status | varchar | Статус: `answered`, `missed`, `busy` |
| recording_url | text | Ссылка на запись |
| transcript | text | Расшифровка |
| raw_data | json | Сырые данные |

## Парк

### `vehicles`
Автомобили из 1С.

| Поле | Тип | Описание |
|------|-----|----------|
| id | bigint PK | Идентификатор |
| plate | varchar | Госномер |
| model | varchar | Модель |
| year | int | Год выпуска |
| status | varchar | Статус: `active`, `repair`, `idle` |

### `drivers`
Водители.

| Поле | Тип | Описание |
|------|-----|----------|
| id | bigint PK | Идентификатор |
| name | varchar | Имя |
| phone_normalized | varchar | Телефон |
| license_category | varchar | Категория прав |

### `transport_orders`
Заказы на перевозку / выдачи авто.

| Поле | Тип | Описание |
|------|-----|----------|
| id | bigint PK | Идентификатор |
| deal_id | bigint FK | Связь со сделкой |
| vehicle_id | bigint FK | Автомобиль |
| driver_id | bigint FK | Водитель |
| route_name | varchar | Маршрут |
| planned_start | timestamptz | Плановое начало |
| actual_end | timestamptz | Фактическое завершение |
| revenue | numeric(15,2) | Выручка |
| cost | numeric(15,2) | Затраты |
| status | varchar | Статус: `completed`, `in_progress`, `cancelled` |

### `repairs`
Ремонты ТС.

| Поле | Тип | Описание |
|------|-----|----------|
| id | bigint PK | Идентификатор |
| vehicle_id | bigint FK | Автомобиль |
| started_at | timestamptz | Начало ремонта |
| ended_at | timestamptz | Завершение |
| cost | numeric(15,2) | Стоимость |
| description | text | Описание |

### `fuel_transactions`
Заправки.

| Поле | Тип | Описание |
|------|-----|----------|
| id | bigint PK | Идентификатор |
| vehicle_id | bigint FK | Автомобиль |
| driver_id | bigint FK | Водитель |
| liters | numeric(10,2) | Литры |
| cost | numeric(15,2) | Стоимость |
| odometer_km | int | Пробег |
| created_at | timestamptz | Время заправки |

## Аналитические витрины

### `mart_call_conversion`
Конверсия звонков по месяцам.

| Поле | Тип | Описание |
|------|-----|----------|
| period | text | Месяц |
| calls | int | Всего звонков |
| calls_with_deal | int | Звонков со сделкой |
| conversion_percent | numeric(5,2) | `calls_with_deal / calls * 100` |

### `mart_vehicle_efficiency`
Эффективность автомобиля.

| Поле | Тип | Описание |
|------|-----|----------|
| vehicle_id | bigint | ID ТС |
| plate | text | Госномер |
| model | text | Модель |
| orders_count | int | Количество заказов |
| total_revenue | numeric(15,2) | Суммарная выручка |
| total_cost | numeric(15,2) | Суммарные затраты |
| profit | numeric(15,2) | `total_revenue - total_cost` |

### `mart_order_profitability`
Прибыльность заказов.

| Поле | Тип | Описание |
|------|-----|----------|
| order_id | bigint | ID заказа |
| deal_title | text | Сделка |
| route_name | text | Маршрут |
| revenue | numeric(15,2) | Выручка |
| cost | numeric(15,2) | Затраты |
| profit | numeric(15,2) | `revenue - cost` |
| margin_percent | numeric(6,2) | `profit / revenue * 100` |
| status | text | Статус |

### `mart_vehicle_downtime`
Простой и ремонты ТС за 12 месяцев.

| Поле | Тип | Описание |
|------|-----|----------|
| vehicle_id | bigint | ID ТС |
| plate | text | Госномер |
| model | text | Модель |
| repairs_count | int | Количество ремонтов |
| downtime_days | numeric(10,2) | Суммарные дни в ремонте |
| repair_cost | numeric(15,2) | Суммарные затраты на ремонт |

### `mart_vehicle_fuel_efficiency`
Расход топлива.

| Поле | Тип | Описание |
|------|-----|----------|
| vehicle_id | bigint | ID ТС |
| plate | text | Госномер |
| model | text | Модель |
| refuels_count | int | Количество заправок |
| total_liters | numeric(12,2) | Сумма литров |
| fuel_cost | numeric(15,2) | Сумма затрат |
| liters_per_100km | numeric(6,2) | `liters / (max_odometer - min_odometer) * 100` |

### `mart_customer_ltv`
LTV клиента.

| Поле | Тип | Описание |
|------|-----|----------|
| contact_id | bigint | ID контакта |
| name | text | Имя |
| phone_normalized | text | Телефон |
| deals_count | int | Сделок |
| orders_count | int | Заказов |
| ltv | numeric(15,2) | Суммарная выручка |
| profit | numeric(15,2) | Суммарная прибыль |

## Связи

- `crm_contacts` → `crm_deals` по `contact_id`
- `crm_contacts` → `calls` по `contact_id` и `phone_normalized`
- `crm_deals` → `calls` по `deal_id`
- `crm_deals` → `transport_orders` по `deal_id`
- `vehicles` → `transport_orders`, `repairs`, `fuel_transactions` по `vehicle_id`
- `drivers` → `transport_orders`, `fuel_transactions` по `driver_id`
