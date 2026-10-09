broker_url = "redis://redis:6379/0"
result_backend = "redis://redis:6379/0"

timezone = "Europe/Moscow"
enable_utc = True

beat_schedule = {
    "sync-bitrix24-daily": {
        "task": "tasks.sync_bitrix24",
        "schedule": 86400.0,
    },
    "sync-uis-daily": {
        "task": "tasks.sync_uis",
        "schedule": 86400.0,
    },
    "sync-1c-daily": {
        "task": "tasks.sync_1c",
        "schedule": 86400.0,
    },
    "recalc-marts-daily": {
        "task": "tasks.recalc_marts",
        "schedule": 86400.0,
    },
}
