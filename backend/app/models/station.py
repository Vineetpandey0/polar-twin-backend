from typing import List, Optional
from sqlalchemy import String, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="OPERATIONAL")
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    assets: Mapped[List["Asset"]] = relationship(
        "Asset", back_populates="station", cascade="all, delete-orphan"
    )
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert", back_populates="station", cascade="all, delete-orphan"
    )
    inventory_items: Mapped[List["InventoryItem"]] = relationship(
        "InventoryItem", back_populates="station", cascade="all, delete-orphan"
    )
