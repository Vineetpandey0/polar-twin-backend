from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.digital_twin.engine import digital_twin_engine

router = APIRouter(prefix="/stations", tags=["Telemetry"])


@router.get("/{station_id}/telemetry")
async def get_station_telemetry(
    station_id: str,
    asset_id: Optional[str] = Query(None),
    metric: Optional[str] = Query(None),
) -> dict:
    st_state = digital_twin_engine.get_station_state(station_id)
    if not st_state:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found")

    readings = []
    for aid, asset in st_state["assets"].items():
        if asset_id and aid != asset_id:
            continue
        for m, val in asset["sensor_readings"].items():
            if metric and m != metric:
                continue
            readings.append({
                "asset_id": aid,
                "metric": m,
                "value": val,
                "timestamp": asset["last_updated"],
            })

    return {"station_id": station_id, "readings": readings, "simulated": True}


@router.get("/{station_id}/telemetry/{asset_id}")
async def get_asset_telemetry(station_id: str, asset_id: str) -> dict:
    asset = digital_twin_engine.get_asset_state(station_id, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found")

    return {
        "station_id": station_id,
        "asset_id": asset_id,
        "readings": asset["sensor_readings"],
        "last_updated": asset["last_updated"],
        "simulated": True,
    }


status_router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@status_router.get("/status")
async def get_telemetry_status() -> dict:
    from datetime import datetime, timezone
    from app.services.ingestion_service import ingestion_service
    from app.websocket.manager import connection_manager
    from app.simulation.live_simulator import live_telemetry_simulator

    now = datetime.now(timezone.utc)
    last_time = ingestion_service.last_telemetry_time
    from app.core.config import settings
    sim_interval = float(getattr(settings, "SIMULATION_INTERVAL_SECONDS", 600.0))
    is_active = ingestion_service.is_active(max_idle_seconds=max(sim_interval * 2.5, 900.0))
    seconds_since_last = round((now - last_time).total_seconds(), 1) if last_time else None

    return {
        "status": "active" if is_active else "idle",
        "simulator_connected": is_active,
        "simulator_running": live_telemetry_simulator.is_running,
        "seconds_since_last_tick": seconds_since_last,
        "last_telemetry_time": last_time.isoformat() if last_time else None,
        "messages_ingested": ingestion_service.messages_ingested_count,
        "active_ws_connections": {
            st: len(conns) for st, conns in connection_manager.active_connections.items()
        },
    }

