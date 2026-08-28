from typing import List
from fastapi import APIRouter, HTTPException
from app.digital_twin.engine import digital_twin_engine
from app.schemas.station import StationResponse, StationSummary

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get("", response_model=List[StationSummary])
async def list_stations() -> List[dict]:
    summaries = []
    for st_id in ["maitri", "bharati"]:
        st_state = digital_twin_engine.get_station_state(st_id)
        if st_state:
            summaries.append({
                "station_id": st_id,
                "name": st_state["name"],
                "location": "Queen Maud Land" if st_id == "maitri" else "Larsemann Hills",
                "latitude": -70.7667 if st_id == "maitri" else -69.4072,
                "longitude": 11.7333 if st_id == "maitri" else 76.1872,
                "status": "OPERATIONAL",
                "health_score": st_state["station_health_score"],
                "active_alert_count": sum(st_state["active_alert_count"].values()),
                "connectivity_status": st_state["connectivity_status"],
                "simulated": True,
            })
    return summaries


@router.get("/{station_id}", response_model=StationResponse)
async def get_station_detail(station_id: str) -> dict:
    st_state = digital_twin_engine.get_station_state(station_id)
    if not st_state:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found")
    return {
        "station_id": st_state["station_id"],
        "name": st_state["name"],
        "location": "Queen Maud Land" if station_id == "maitri" else "Larsemann Hills",
        "latitude": -70.7667 if station_id == "maitri" else -69.4072,
        "longitude": 11.7333 if station_id == "maitri" else 76.1872,
        "status": "OPERATIONAL",
        "station_health_score": st_state["station_health_score"],
        "connectivity_status": st_state["connectivity_status"],
        "active_alert_count": st_state["active_alert_count"],
        "energy_balance": st_state["energy_balance"],
        "assets": st_state["assets"],
        "last_updated": st_state["last_updated"],
        "simulated": True,
    }


@router.get("/{station_id}/assets")
async def list_station_assets(station_id: str) -> dict:
    st_state = digital_twin_engine.get_station_state(station_id)
    if not st_state:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found")
    return {"station_id": station_id, "assets": st_state["assets"], "simulated": True}


@router.get("/{station_id}/assets/{asset_id}")
async def get_asset_detail(station_id: str, asset_id: str) -> dict:
    asset = digital_twin_engine.get_asset_state(station_id, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found")
    return {
        "asset_id": asset["asset_id"],
        "station_id": asset["station_id"],
        "name": asset["name"],
        "type": asset["asset_type"],
        "status": asset["operational_status"],
        "health_score": asset["health_score"],
        "state": asset,
        "simulated": True,
    }
