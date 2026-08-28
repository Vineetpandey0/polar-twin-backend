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
