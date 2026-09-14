from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.core.database import get_db
from app.models.maintenance import MaintenanceRecord
from app.models.asset import Asset

router = APIRouter(prefix="", tags=["Maintenance"])


class MaintenanceUpdateRequest(BaseModel):
    status: str  # PENDING / IN_PROGRESS / COMPLETED
    completed_notes: Optional[str] = None


def format_maintenance_record(rec: MaintenanceRecord, asset: Optional[Asset] = None) -> dict:
    return {
        "id": rec.id,
        "asset_id": rec.asset_id,
        "asset_name": asset.name if asset else rec.asset_id,
        "station_id": asset.station_id if asset else ("maitri" if "MAI" in rec.asset_id else "bharati"),
        "title": rec.title,
        "description": rec.description,
        "priority": rec.priority,
        "status": rec.status,
        "scheduled_date": rec.scheduled_date.isoformat() if rec.scheduled_date else None,
        "completed_at": rec.completed_at.isoformat() if rec.completed_at else None,
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
    }


@router.get("/maintenance")
async def get_all_maintenance(
    station_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    query = select(MaintenanceRecord, Asset).outerjoin(Asset, MaintenanceRecord.asset_id == Asset.id).order_by(desc(MaintenanceRecord.scheduled_date))

    if status and isinstance(status, str) and status.upper() != "ALL":
        query = query.where(MaintenanceRecord.status == status.upper())
    if priority and isinstance(priority, str) and priority.upper() != "ALL":
        query = query.where(MaintenanceRecord.priority == priority.upper())

    result = await db.execute(query)
    rows = result.all()

    formatted = []
    for rec, asset in rows:
        item = format_maintenance_record(rec, asset)
        if station_id and isinstance(station_id, str) and station_id.upper() != "ALL":
            if item["station_id"].lower() != station_id.lower():
                continue
        formatted.append(item)

    return formatted


@router.get("/stations/{station_id}/maintenance")
async def get_station_maintenance(
    station_id: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    return await get_all_maintenance(station_id=station_id, status=status, priority=priority, db=db)


@router.patch("/maintenance/{record_id}")
async def update_maintenance_status(
    record_id: int,
    req: MaintenanceUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(MaintenanceRecord).where(MaintenanceRecord.id == record_id))
    rec = result.scalars().first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Maintenance record {record_id} not found in database.")

    rec.status = req.status.upper()
    if req.status.upper() == "COMPLETED":
        rec.completed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(rec)
    return format_maintenance_record(rec)
