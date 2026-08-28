from fastapi import APIRouter
from app.api.v1.stations import router as stations_router
from app.api.v1.telemetry import router as telemetry_router
from app.api.v1.energy import router as energy_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.scenarios import router as scenarios_router
from app.api.v1.ai import router as ai_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(stations_router)
api_v1_router.include_router(telemetry_router)
api_v1_router.include_router(energy_router)
api_v1_router.include_router(alerts_router)
api_v1_router.include_router(inventory_router)
api_v1_router.include_router(scenarios_router)
api_v1_router.include_router(ai_router)
