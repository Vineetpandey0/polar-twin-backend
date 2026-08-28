from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any


@dataclass
class AssetStateData:
    asset_id: str
    station_id: str
    name: str
    asset_type: str
    operational_status: str = "RUNNING"
    health_score: float = 1.0
    failure_probability: float = 0.02
    anomaly_score: float = 0.01
    connectivity: str = "LIVE"
    sensor_readings: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "station_id": self.station_id,
            "name": self.name,
            "asset_type": self.asset_type,
            "operational_status": self.operational_status,
            "health_score": round(self.health_score, 2),
            "failure_probability": round(self.failure_probability, 2),
            "anomaly_score": round(self.anomaly_score, 2),
            "connectivity": self.connectivity,
            "sensor_readings": self.sensor_readings,
            "last_updated": self.last_updated.isoformat(),
            "simulated": True,
        }


@dataclass
class StationStateData:
    station_id: str
    name: str
    station_health_score: float = 1.0
    connectivity_status: str = "LIVE"
    active_alert_count: Dict[str, int] = field(
        default_factory=lambda: {"INFO": 0, "WARNING": 0, "CRITICAL": 0}
    )
    energy_balance: Dict[str, float] = field(
        default_factory=lambda: {"generation_kw": 0.0, "consumption_kw": 0.0, "net_balance_kw": 0.0}
    )
    assets: Dict[str, AssetStateData] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "station_id": self.station_id,
            "name": self.name,
            "station_health_score": round(self.station_health_score, 2),
            "connectivity_status": self.connectivity_status,
            "active_alert_count": self.active_alert_count,
            "energy_balance": self.energy_balance,
            "assets": {aid: asset.to_dict() for aid, asset in self.assets.items()},
            "last_updated": self.last_updated.isoformat(),
            "simulated": True,
        }
