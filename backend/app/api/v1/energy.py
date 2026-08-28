from fastapi import APIRouter, HTTPException
from app.digital_twin.engine import digital_twin_engine
from app.analytics.energy_forecaster import energy_forecaster

router = APIRouter(prefix="/stations", tags=["Energy"])


@router.get("/{station_id}/energy")
async def get_station_energy(station_id: str) -> dict:
    st_state = digital_twin_engine.get_station_state(station_id)
    if not st_state:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found")

    generators = {
        aid: a["sensor_readings"]
        for aid, a in st_state["assets"].items()
        if a["asset_type"] == "GENERATOR"
    }
    batteries = {
        aid: a["sensor_readings"]
        for aid, a in st_state["assets"].items()
        if a["asset_type"] == "BATTERY"
    }

    return {
        "station_id": station_id,
        "energy_balance": st_state["energy_balance"],
        "generators": generators,
        "batteries": batteries,
        "simulated": True,
    }


@router.get("/{station_id}/energy/forecast")
async def get_energy_forecast(station_id: str) -> dict:
    st_state = digital_twin_engine.get_station_state(station_id)
    if not st_state:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found")

    ambient_temp = -25.0 if station_id == "maitri" else -18.0
    forecasts = energy_forecaster.forecast_24h(station_id, ambient_temp)

    return {
        "station_id": station_id,
        "forecast_horizon_hours": 24,
        "model_type": "RandomForestRegressor",
        "forecasts": forecasts,
    }
