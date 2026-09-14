import asyncio
import logging
from typing import List, Dict
from datetime import datetime, timezone
from app.schemas.alert import AlertCreate
from app.alerts.rule_engine import rule_engine
from app.models.alert import Alert
from app.core.database import AsyncSessionLocal

logger = logging.getLogger("alert_service")


class AlertService:
    def __init__(self) -> None:
        self.active_alerts: List[dict] = []
        self._next_id = 100

    async def _persist_to_db(self, new_alert: AlertCreate):
        try:
            async with AsyncSessionLocal() as session:
                db_alert = Alert(
                    station_id=new_alert.station_id,
                    asset_id=new_alert.asset_id,
                    severity=new_alert.severity,
                    title=new_alert.message,
                    message=new_alert.message,
                    reason=new_alert.reason,
                    remedy="Follow standard Antarctic SCADA troubleshooting protocol.",
                    acknowledged=False,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(db_alert)
                await session.commit()
                logger.info(f"Persisted alert to database: {new_alert.message}")
        except Exception as e:
            logger.warning(f"Could not persist alert to database: {e}")

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
                    "asset_id": new_alert.asset_id or "STATION-WIDE",
                    "severity": new_alert.severity,
                    "title": new_alert.message,
                    "message": new_alert.message,
                    "reason": new_alert.reason,
                    "remedy": "Follow standard Antarctic SCADA troubleshooting protocol.",
                    "acknowledged": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                self._next_id += 1
                self.active_alerts.append(alert_dict)
                created_now.append(alert_dict)
                logger.info(f"New alert triggered: [{new_alert.severity}] {new_alert.message}")

                # Schedule DB persistence
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self._persist_to_db(new_alert))
                except RuntimeError:
                    pass

        return created_now


alert_service = AlertService()
