from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class AlertBase(BaseModel):
    station_id: str
    asset_id: Optional[str] = None
    severity: str  # INFO / WARNING / CRITICAL
    message: str
    reason: str


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: int
    created_at: datetime
    resolved_at: Optional[datetime] = None
    simulated: bool = True
