import logging
from app.schemas.telemetry import TelemetryMessage
from app.digital_twin.engine import digital_twin_engine

logger = logging.getLogger("ingestion_service")


class IngestionService:
    async def process(self, telemetry: TelemetryMessage) -> None:
        try:
            # 1. Update live Digital Twin engine state
            digital_twin_engine.update_asset_state(
                station_id=telemetry.station_id,
                asset_id=telemetry.asset_id,
                metric=telemetry.metric,
                value=telemetry.value,
                timestamp=telemetry.timestamp,
            )
        except Exception as e:
            logger.error(f"Error processing telemetry message: {e}")


ingestion_service = IngestionService()
