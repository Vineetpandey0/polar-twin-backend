from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="", tags=["Alerts"])

# In-memory mock alerts list for active status
mock_alerts = [
    {
        "id": 1,
        "station_id": "maitri",
        "asset_id": "GEN-MAI-001",
        "severity": "WARNING",
        "message": "Generator 1 operating temperature elevated",
        "reason": "Temperature reached 88.5°C threshold",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "resolved_at": None,
        "acknowledged": False,
        "simulated": True,
    }
]


@router.get("/stations/{station_id}/alerts")
async def get_station_alerts(
    station_id: str, severity: Optional[str] = Query(None)
) -> List[dict]:
    res = [a for a in mock_alerts if a["station_id"] == station_id.lower()]
    if severity:
        res = [a for a in res if a["severity"] == severity.upper()]
    return res


@router.patch("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int) -> dict:
    for a in mock_alerts:
        if a["id"] == alert_id:
            a["acknowledged"] = True
            return {"status": "acknowledged", "alert": a}
    raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
