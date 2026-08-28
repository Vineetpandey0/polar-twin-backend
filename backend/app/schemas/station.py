from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel


class StationSummary(BaseModel):
    station_id: str
    name: str
    location: str
    latitude: float
    longitude: float
    status: str
    health_score: float
    active_alert_count: int
    connectivity_status: str
    simulated: bool = True


class StationResponse(BaseModel):
    station_id: str
    name: str
    location: str
    latitude: float
    longitude: float
    status: str
    station_health_score: float
    connectivity_status: str
    active_alert_count: Dict[str, int]
    energy_balance: Dict[str, float]
    assets: Dict[str, dict]
    last_updated: datetime
    simulated: bool = True
