"""
Модели SQLAlchemy и подключение к БД.

Здесь собраны все ORM-модели проекта: сырые события, CRM, телефония,
парк и операционные таблицы. Alembic использует эти модели для генерации миграций.
"""

from sqlalchemy import (
    Column, Integer, String, BigInteger, Numeric, DateTime, Text, JSON,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import select as _select
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://fleet:fleet@localhost:5432/fleet_analytics"
)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()
select = _select


async def get_db():
    """Асинхронная зависимость FastAPI для получения сессии БД."""
    async with AsyncSessionLocal() as session:
        yield session


class SyncState(Base):
    """Состояние синхронизации с внешними системами."""
    __tablename__ = "sync_state"
    id = Column(Integer, primary_key=True)
    source = Column(String, unique=True, nullable=False)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RawEvent(Base):
    """Сырые события из webhook-ов всех источников."""
    __tablename__ = "raw_events"
    id = Column(BigInteger, primary_key=True)
    source = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CRMContact(Base):
    """Контакты из Битрикс24."""
    __tablename__ = "crm_contacts"
    id = Column(BigInteger, primary_key=True)
    bitrix_id = Column(BigInteger, unique=True)
    name = Column(String)
    phone_normalized = Column(String, index=True)
    email = Column(String)
    source_updated_at = Column(DateTime(timezone=True))
    raw_data = Column(JSON)


class CRMDeal(Base):
    """Сделки из Битрикс24."""
    __tablename__ = "crm_deals"
    id = Column(BigInteger, primary_key=True)
    bitrix_id = Column(BigInteger, unique=True)
    title = Column(String)
    stage_id = Column(String)
    pipeline_id = Column(String)
    amount = Column(Numeric(15, 2))
    responsible_id = Column(BigInteger)
    contact_id = Column(BigInteger, ForeignKey("crm_contacts.id"))
    company_id = Column(BigInteger)
    created_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))
    raw_data = Column(JSON)


class Call(Base):
    """Звонки из UIS."""
    __tablename__ = "calls"
    id = Column(BigInteger, primary_key=True)
    provider = Column(String, nullable=False)
    provider_call_id = Column(String, nullable=False)
    bitrix_activity_id = Column(BigInteger)
    direction = Column(String)
    phone_normalized = Column(String, index=True)
    employee_id = Column(BigInteger)
    contact_id = Column(BigInteger, ForeignKey("crm_contacts.id"))
    company_id = Column(BigInteger)
    lead_id = Column(BigInteger)
    deal_id = Column(BigInteger, ForeignKey("crm_deals.id"))
    started_at = Column(DateTime(timezone=True))
    answered_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    duration_sec = Column(Integer)
    wait_duration_sec = Column(Integer)
    status = Column(String)
    recording_url = Column(Text)
    transcript = Column(Text)
    raw_data = Column(JSON)
    __table_args__ = (UniqueConstraint("provider", "provider_call_id"),)


class Vehicle(Base):
    """Автомобили из 1С."""
    __tablename__ = "vehicles"
    id = Column(BigInteger, primary_key=True)
    plate = Column(String, unique=True)
    model = Column(String)
    year = Column(Integer)
    status = Column(String)


class Driver(Base):
    """Водители."""
    __tablename__ = "drivers"
    id = Column(BigInteger, primary_key=True)
    name = Column(String)
    phone_normalized = Column(String, index=True)
    license_category = Column(String)


class TransportOrder(Base):
    """Заказы на перевозку / выдачи автомобилей."""
    __tablename__ = "transport_orders"
    id = Column(BigInteger, primary_key=True)
    deal_id = Column(BigInteger, ForeignKey("crm_deals.id"), nullable=True)
    vehicle_id = Column(BigInteger, ForeignKey("vehicles.id"), nullable=True)
    driver_id = Column(BigInteger, ForeignKey("drivers.id"), nullable=True)
    route_name = Column(String)
    planned_start = Column(DateTime(timezone=True))
    actual_end = Column(DateTime(timezone=True))
    revenue = Column(Numeric(15, 2))
    cost = Column(Numeric(15, 2))
    status = Column(String)


class Repair(Base):
    """Ремонты транспортных средств."""
    __tablename__ = "repairs"
    id = Column(BigInteger, primary_key=True)
    vehicle_id = Column(BigInteger, ForeignKey("vehicles.id"))
    started_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))
    cost = Column(Numeric(15, 2))
    description = Column(Text)


class FuelTransaction(Base):
    """Заправки топлива."""
    __tablename__ = "fuel_transactions"
    id = Column(BigInteger, primary_key=True)
    vehicle_id = Column(BigInteger, ForeignKey("vehicles.id"))
    driver_id = Column(BigInteger, ForeignKey("drivers.id"))
    liters = Column(Numeric(10, 2))
    cost = Column(Numeric(15, 2))
    odometer_km = Column(Integer)
    created_at = Column(DateTime(timezone=True))
