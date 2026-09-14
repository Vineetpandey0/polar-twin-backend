from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.core.database import get_db
from app.models.alert import Alert

router = APIRouter(prefix="", tags=["Alerts"])


class AlertResponse(BaseModel):
    id: int
    station_id: str
    asset_id: Optional[str] = None
    severity: str
    title: Optional[str] = None
    message: str
    reason: str
    remedy: Optional[str] = None
    acknowledged: bool
    created_at: str
    resolved_at: Optional[str] = None

    class Config:
        from_attributes = True


class AlertCreateRequest(BaseModel):
    station_id: str
    asset_id: Optional[str] = None
    severity: str = "WARNING"
    title: Optional[str] = None
    message: str
    reason: str
    remedy: Optional[str] = None


def format_alert(a: Alert) -> dict:
    return {
        "id": a.id,
        "station_id": a.station_id,
        "asset_id": a.asset_id or "STATION-WIDE",
        "severity": a.severity,
        "title": a.title or a.message,
        "message": a.message,
        "reason": a.reason,
        "remedy": a.remedy or "Inspect subsystem status according to station standard operating procedures.",
        "acknowledged": bool(a.acknowledged),
        "created_at": a.created_at.isoformat() if a.created_at else datetime.now(timezone.utc).isoformat(),
        "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
    }


@router.get("/alerts")
async def get_all_alerts(
    station_id: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None, # ACTIVE / ACKNOWLEDGED / ALL
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    query = select(Alert).order_by(desc(Alert.created_at))

    if station_id and isinstance(station_id, str) and station_id.upper() != "ALL":
        query = query.where(Alert.station_id == station_id.lower())
    if severity and isinstance(severity, str) and severity.upper() != "ALL":
        query = query.where(Alert.severity == severity.upper())
    if status == "ACTIVE":
        query = query.where(Alert.acknowledged == False)
    elif status == "ACKNOWLEDGED":
        query = query.where(Alert.acknowledged == True)

    result = await db.execute(query)
    alerts = result.scalars().all()
    return [format_alert(a) for a in alerts]


@router.get("/stations/{station_id}/alerts")
async def get_station_alerts(
    station_id: str,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    return await get_all_alerts(station_id=station_id, severity=severity, status=status, db=db)


@router.patch("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalars().first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found in database")

    alert.acknowledged = True
    alert.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(alert)

    return {
        "status": "acknowledged",
        "alert": format_alert(alert),
    }


@router.post("/alerts")
async def create_alert(
    req: AlertCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    new_alert = Alert(
        station_id=req.station_id.lower(),
        asset_id=req.asset_id,
        severity=req.severity.upper(),
        title=req.title or req.message,
        message=req.message,
        reason=req.reason,
        remedy=req.remedy,
        acknowledged=False,
    )
    db.add(new_alert)
    await db.commit()
    await db.refresh(new_alert)
    return format_alert(new_alert)
