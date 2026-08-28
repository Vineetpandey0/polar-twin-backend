import logging
from typing import List, Dict
from app.schemas.alert import AlertCreate
from app.alerts.rule_engine import rule_engine

logger = logging.getLogger("alert_service")


class AlertService:
    def __init__(self) -> None:
        self.active_alerts: List[dict] = []
        self._next_id = 1

    def process_station_state(self, station_state: Dict) -> List[dict]:
        triggered = rule_engine.evaluate_station(station_state)
        created_now = []

        for new_alert in triggered:
            # Deduplication check
            exists = any(
                a["station_id"] == new_alert.station_id
                and a["asset_id"] == new_alert.asset_id
                and a["severity"] == new_alert.severity
                and a["reason"] == new_alert.reason
                for a in self.active_alerts
            )
            if not exists:
                alert_dict = {
                    "id": self._next_id,
                    "station_id": new_alert.station_id,
                    "asset_id": new_alert.asset_id,
                    "severity": new_alert.severity,
                    "message": new_alert.message,
                    "reason": new_alert.reason,
                    "acknowledged": False,
                    "simulated": True,
                }
                self._next_id += 1
                self.active_alerts.append(alert_dict)
                created_now.append(alert_dict)
                logger.info(f"New alert triggered: [{new_alert.severity}] {new_alert.message}")

        return created_now


alert_service = AlertService()
