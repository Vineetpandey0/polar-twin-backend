from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any
from app.digital_twin.state import StationStateData, AssetStateData
from app.analytics.anomaly_detector import anomaly_detector
from app.analytics.health_scorer import health_scorer


class DigitalTwinEngine:
    def __init__(self) -> None:
        self.stations: Dict[str, StationStateData] = {
            "maitri": StationStateData(station_id="maitri", name="Maitri Research Station"),
            "bharati": StationStateData(station_id="bharati", name="Bharati Research Station"),
        }
        self._init_default_assets()

    def _init_default_assets(self) -> None:
        maitri_assets = [
            ("BLD-MAI-MAIN", "Maitri Main Station Complex", "BUILDING"),
            ("GEN-MAI-001", "Primary Diesel Generator 1", "GENERATOR"),
            ("GEN-MAI-002", "Primary Diesel Generator 2", "GENERATOR"),
            ("GEN-MAI-003", "Standby Emergency Generator 3", "GENERATOR"),
            ("BAT-MAI-001", "Battery Energy Storage Bank A (BESS)", "BATTERY"),
            ("SWG-MAI-001", "Central Microgrid Switchgear", "SWITCHGEAR"),
            ("FUL-MAI-001", "Polar Diesel Storage Tank 01", "FUEL_TANK"),
            ("FUL-MAI-002", "Polar Diesel Storage Tank 02", "FUEL_TANK"),
            ("PMP-MAI-FUEL", "Fuel Transfer Pump Skid", "PUMP"),
            ("PMP-MAI-LAKE", "Lake Priyadarshini Pump House", "WATER"),
            ("WTR-MAI-001", "Priyadarshini Water Treatment Plant", "WATER"),
            ("AWS-MAI-001", "Automatic Weather Station (AWS)", "SCIENCE"),
            ("COM-MAI-001", "Ku-Band Satellite Ground Station Radome", "COMMS"),
            ("HVC-MAI-001", "Central HVAC & Hydronic Loop", "HVAC"),
            ("HLP-MAI-001", "Maitri Polar Helipad Deck", "LOGISTICS"),
        ]
        for aid, name, atype in maitri_assets:
            self.stations["maitri"].assets[aid] = AssetStateData(
                asset_id=aid, station_id="maitri", name=name, asset_type=atype
            )

        bharati_assets = [
            ("BLD-BHA-MAIN", "Bharati Station Superstructure", "BUILDING"),
            ("GEN-BHA-001", "Combined Heat & Power (CHP) Unit 1", "GENERATOR"),
            ("GEN-BHA-002", "Combined Heat & Power (CHP) Unit 2", "GENERATOR"),
            ("BAT-BHA-001", "Main High-Capacity BESS Array", "BATTERY"),
            ("SWG-BHA-001", "Microgrid Synchronous Switchboard", "SWITCHGEAR"),
            ("FUL-BHA-001", "Bulk Fuel Tank Battery", "FUEL_TANK"),
            ("PMP-BHA-SEA", "Coastal Sea-Water Pump House", "WATER"),
            ("WTR-BHA-001", "Reverse Osmosis (RO) Desalination Plant", "WATER"),
            ("COM-BHA-001", "Dual Tracking Satcom Radomes", "COMMS"),
            ("HLP-BHA-001", "Certified Aviation Helipad Platform", "LOGISTICS"),
        ]
        for aid, name, atype in bharati_assets:
            self.stations["bharati"].assets[aid] = AssetStateData(
                asset_id=aid, station_id="bharati", name=name, asset_type=atype
            )

    def update_asset_state(
        self,
        station_id: str,
        asset_id: str,
        metric: str,
        value: float,
        timestamp: Optional[datetime] = None,
    ) -> None:
        st_id = station_id.lower()
        if st_id not in self.stations:
            return

        station = self.stations[st_id]
        if asset_id not in station.assets:
            station.assets[asset_id] = AssetStateData(
                asset_id=asset_id, station_id=st_id, name=asset_id, asset_type="GENERIC"
            )

        asset = station.assets[asset_id]
        now = timestamp or datetime.now(timezone.utc)
        asset.sensor_readings[metric] = value
        asset.last_updated = now
        asset.connectivity = "LIVE"

        # Update specific operational statuses based on metric
        if metric == "status":
            asset.operational_status = "FAILED" if value == 0.0 else "RUNNING"

        self._evaluate_health_and_energy(st_id)

    def _evaluate_health_and_energy(self, station_id: str) -> None:
        station = self.stations[station_id]
        now = datetime.now(timezone.utc)
        total_health = 0.0
        count = len(station.assets)

        for asset in station.assets.values():
            if (now - asset.last_updated) > timedelta(minutes=5):
                asset.connectivity = "STALE"

            asset_dict = asset.to_dict()
            h_score, f_prob, rul = health_scorer.score_asset(asset_dict)
            anomaly_score, _ = anomaly_detector.predict_anomaly(asset.sensor_readings)

            asset.health_score = h_score
            asset.failure_probability = f_prob
            asset.anomaly_score = anomaly_score

            total_health += asset.health_score

        station.station_health_score = round(total_health / count, 3) if count > 0 else 1.0
        station.last_updated = now

    def get_station_state(self, station_id: str) -> Optional[Dict[str, Any]]:
        st_id = station_id.lower()
        if st_id not in self.stations:
            return None
        self._evaluate_health_and_energy(st_id)
        return self.stations[st_id].to_dict()

    def get_asset_state(self, station_id: str, asset_id: str) -> Optional[Dict[str, Any]]:
        st_id = station_id.lower()
        if st_id not in self.stations or asset_id not in self.stations[st_id].assets:
            return None
        return self.stations[st_id].assets[asset_id].to_dict()


# Global Singleton
digital_twin_engine = DigitalTwinEngine()
