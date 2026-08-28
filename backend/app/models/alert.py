from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("stations.id"), nullable=False
    )
    asset_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("assets.id"), nullable=True
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # INFO / WARNING / CRITICAL
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    resolved_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    station: Mapped["Station"] = relationship("Station", back_populates="alerts")
    asset: Mapped[Optional["Asset"]] = relationship("Asset", back_populates="alerts")
