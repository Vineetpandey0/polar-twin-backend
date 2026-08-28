from datetime import datetime
from pydantic import BaseModel


class TelemetryMessage(BaseModel):
    station_id: str
    asset_id: str
    sensor_id: str
    metric: str
    value: float
    unit: str
    timestamp: datetime
