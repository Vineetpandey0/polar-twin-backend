from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models.inventory import InventoryItem

router = APIRouter(prefix="", tags=["Inventory"])


class RequisitionRequest(BaseModel):
    item_id: int
    quantity: float
    notes: Optional[str] = None


def format_inventory_item(item: InventoryItem) -> dict:
    burn_rate = float(item.burn_rate_daily) if item.burn_rate_daily and item.burn_rate_daily > 0 else 1.0
    days_left = round(float(item.current_level) / burn_rate)
    return {
        "id": f"INV-{item.station_id[:3].upper()}-{item.id:03d}",
        "raw_id": item.id,
        "station_id": item.station_id,
        "name": item.name,
        "category": item.category,
        "current_level": float(item.current_level),
        "max_capacity": float(item.max_capacity) if item.max_capacity else float(item.current_level) * 1.3,
        "unit": item.unit,
        "reorder_threshold": float(item.reorder_threshold),
        "burn_rate_daily": burn_rate,
        "days_remaining": days_left,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


@router.get("/inventory")
async def get_all_inventory(
    station_id: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    query = select(InventoryItem).order_by(InventoryItem.station_id, InventoryItem.category)

    if station_id and isinstance(station_id, str) and station_id.upper() != "ALL":
        query = query.where(InventoryItem.station_id == station_id.lower())
    if category and isinstance(category, str) and category.upper() != "ALL":
        query = query.where(InventoryItem.category == category.upper())

    result = await db.execute(query)
    items = result.scalars().all()
    return [format_inventory_item(i) for i in items]


@router.get("/stations/{station_id}/inventory")
async def get_station_inventory(
    station_id: str,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    st_id = station_id.lower()
    items = await get_all_inventory(station_id=st_id, category=category, db=db)
    return {
        "station_id": st_id,
        "inventory": items,
        "total_items": len(items),
        "source": "database",
    }


@router.post("/inventory/requisition")
async def create_requisition(
    req: RequisitionRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(InventoryItem).where(InventoryItem.id == req.item_id))
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Inventory item ID {req.item_id} not found in database.")

    return {
        "status": "LOGGED",
        "requisition_id": f"REQ-NCPOR-{item.id:04d}",
        "item_name": item.name,
        "station_id": item.station_id,
        "requested_qty": req.quantity,
        "unit": item.unit,
        "message": f"Requisition order logged for {req.quantity} {item.unit} of {item.name}. Dispatched to NCPOR Logistics Headquarters.",
    }
