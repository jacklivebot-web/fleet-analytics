"""
Точка входа FastAPI.

Собирает все роутеры проекта и управляет жизненным циклом приложения.
Схема БД управляется через Alembic, поэтому create_all отключён —
иначе Alembic и приложение будут друг друга перебивать.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from models import engine

import routers.sync
import routers.webhooks
import routers.health
import routers.analytics
import routers.mock_services
import routers.scheduler
import routers.data_quality


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Жизненный цикл приложения.

    Создание таблиц отключено: управление схемой выполняется Alembic.
    При необходимости можно раскомментировать create_all для локального dev,
    но тогда Alembic надо применять после.
    """
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Fleet Analytics Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Подключаем роутеры
app.include_router(routers.health.router)
app.include_router(routers.webhooks.router, prefix="/webhooks")
app.include_router(routers.sync.router, prefix="/sync")
app.include_router(routers.analytics.router, prefix="/analytics")
app.include_router(routers.mock_services.router, prefix="/mock")
app.include_router(routers.scheduler.router, prefix="/scheduler")
app.include_router(routers.data_quality.router, prefix="/data-quality")
