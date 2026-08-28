from typing import List, Optional
from sqlalchemy import String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    station_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("stations.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="RUNNING")
    health_score: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    station: Mapped["Station"] = relationship("Station", back_populates="assets")
    sensor_readings: Mapped[List["SensorReading"]] = relationship(
        "SensorReading", back_populates="asset", cascade="all, delete-orphan"
    )
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert", back_populates="asset", cascade="all, delete-orphan"
    )
    maintenance_records: Mapped[List["MaintenanceRecord"]] = relationship(
        "MaintenanceRecord", back_populates="asset", cascade="all, delete-orphan"
    )
