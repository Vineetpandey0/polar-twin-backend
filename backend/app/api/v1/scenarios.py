from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.simulation.scenario_engine import scenario_engine

router = APIRouter(prefix="/stations", tags=["Scenarios"])


class ScenarioRunRequest(BaseModel):
    scenario: str  # generator_failure / extreme_weather / comms_loss / fuel_critical


@router.post("/{station_id}/scenarios/run")
async def run_scenario_endpoint(station_id: str, req: ScenarioRunRequest) -> dict:
    res = scenario_engine.run_scenario(station_id, req.scenario)
    if not res:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found")
    return res
