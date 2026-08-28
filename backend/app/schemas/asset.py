from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel


class AssetState(BaseModel):
    asset_id: str
    station_id: str
    name: str
    asset_type: str
    operational_status: str  # RUNNING / STOPPED / FAILED / MAINTENANCE
    health_score: float
    failure_probability: float
    anomaly_score: float
    connectivity: str  # LIVE / STALE / OFFLINE
    sensor_readings: Dict[str, float]
    last_updated: datetime
    simulated: bool = True


class AssetResponse(BaseModel):
    asset_id: str
    station_id: str
    name: str
    type: str
    status: str
    health_score: float
    state: AssetState
    simulated: bool = True
