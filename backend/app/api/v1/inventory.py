from fastapi import APIRouter, HTTPException
from app.digital_twin.engine import digital_twin_engine

router = APIRouter(prefix="/stations", tags=["Inventory"])


@router.get("/{station_id}/inventory")
async def get_station_inventory(station_id: str) -> dict:
    st_id = station_id.lower()
    if st_id not in ["maitri", "bharati"]:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found")

    items = [
        {"name": "Arctic High-Grade Diesel", "category": "FUEL", "current_level": 45000 if st_id == "maitri" else 60000, "unit": "LITERS", "reorder_threshold": 15000},
        {"name": "Ration & Dry Food Reserves", "category": "FOOD", "current_level": 120 if st_id == "maitri" else 180, "unit": "DAYS", "reorder_threshold": 30},
        {"name": "Medical Trauma Kit & Supplies", "category": "MEDICAL", "current_level": 100, "unit": "PCT", "reorder_threshold": 40},
        {"name": "Spare Components Array", "category": "SPARE_PARTS", "current_level": 25 if st_id == "maitri" else 30, "unit": "UNITS", "reorder_threshold": 5},
    ]

    return {"station_id": st_id, "inventory": items, "simulated": True}
