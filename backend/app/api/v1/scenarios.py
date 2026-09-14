from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.simulation.scenario_engine import scenario_engine

router = APIRouter(prefix="/stations", tags=["Scenarios"])


class ScenarioRunRequest(BaseModel):
    scenario: str
    custom_params: Optional[Dict[str, Any]] = None


@router.get("/scenarios/catalog")
async def get_scenarios_catalog() -> List[dict]:
    return scenario_engine.get_catalog()


@router.get("/{station_id}/scenarios/catalog")
async def get_station_scenarios_catalog(station_id: str) -> List[dict]:
    return scenario_engine.get_catalog()


@router.post("/{station_id}/scenarios/run")
async def run_scenario_endpoint(station_id: str, req: ScenarioRunRequest) -> dict:
    st_id = station_id.lower()
    if st_id not in ["maitri", "bharati"]:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found")

    res = scenario_engine.run_scenario(
        station_id=st_id,
        scenario_name=req.scenario,
        custom_params=req.custom_params,
    )
    return res
