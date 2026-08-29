import logging
from datetime import datetime, timezone
from app.schemas.telemetry import TelemetryMessage
from app.digital_twin.engine import digital_twin_engine
from app.websocket.manager import connection_manager
from app.core.database import AsyncSessionLocal
from app.models.sensor_reading import SensorReading

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

            # 2. Broadcast live update to connected WebSockets
            await connection_manager.broadcast(
                telemetry.station_id,
                {
                    "type": "telemetry_update",
                    "station_id": telemetry.station_id,
                    "asset_id": telemetry.asset_id,
                    "metric": telemetry.metric,
                    "value": telemetry.value,
                    "unit": telemetry.unit,
                    "timestamp": telemetry.timestamp.isoformat() if telemetry.timestamp else None,
                },
            )

            # 3. Persist telemetry reading to database table sensor_readings
            try:
                async with AsyncSessionLocal() as session:
                    # Verify if asset exists in DB table assets, if not create it
                    from sqlalchemy import select
                    from app.models.asset import Asset

                    asset_res = await session.execute(select(Asset).where(Asset.id == telemetry.asset_id))
                    asset_obj = asset_res.scalar_one_or_none()

                    if not asset_obj:
                        new_asset = Asset(
                            id=telemetry.asset_id,
                            station_id=telemetry.station_id,
                            name=telemetry.asset_id,
                            type="ENVIRONMENT" if "ENV" in telemetry.asset_id else "GENERIC",
                            status="RUNNING",
                            health_score=1.0,
                        )
                        session.add(new_asset)
                        await session.flush()

                    reading = SensorReading(
                        asset_id=telemetry.asset_id,
                        sensor_id=telemetry.sensor_id or f"SEN-{telemetry.asset_id}",
                        metric=telemetry.metric,
                        value=float(telemetry.value),
                        unit=telemetry.unit or "",
                        timestamp=telemetry.timestamp or datetime.now(timezone.utc),
                    )
                    session.add(reading)
                    await session.commit()
            except Exception as db_err:
                logger.error(f"Failed to persist sensor reading to database for {telemetry.asset_id}: {db_err}")

        except Exception as e:
            logger.error(f"Error processing telemetry message: {e}")


ingestion_service = IngestionService()
