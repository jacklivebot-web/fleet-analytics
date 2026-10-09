from contextlib import asynccontextmanager
from fastapi import FastAPI
from models import engine, Base
import routers.sync
import routers.webhooks
import routers.health
import routers.analytics
import routers.mock_services
import routers.scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables are managed by Alembic migrations; create_all is disabled for production.
    # For local/dev convenience, uncomment the next two lines if migrations are not applied.
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title="Fleet Analytics Platform", version="0.1.0", lifespan=lifespan)

app.include_router(routers.health.router)
app.include_router(routers.webhooks.router, prefix="/webhooks")
app.include_router(routers.sync.router, prefix="/sync")
app.include_router(routers.analytics.router, prefix="/analytics")
app.include_router(routers.mock_services.router, prefix="/mock")
app.include_router(routers.scheduler.router, prefix="/scheduler")
