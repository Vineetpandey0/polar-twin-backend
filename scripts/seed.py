import sys
import os
import asyncio

# Ensure backend path is resolvable
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from app.models.base import Base
    from app.models.station import Station
    from app.models.asset import Asset
    from app.models.inventory import InventoryItem
    from app.core.config import settings
except ImportError:
    from backend.app.models.base import Base
    from backend.app.models.station import Station
    from backend.app.models.asset import Asset
    from backend.app.models.inventory import InventoryItem
    from backend.app.core.config import settings

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def seed_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Check existing stations
        res = await session.get(Station, "maitri")
        if res:
            print("Database already seeded.")
            return

        # Stations
        maitri = Station(
            id="maitri",
            name="Maitri Research Station",
            location="Schirmacher Oasis, Queen Maud Land",
            latitude=-70.7667,
            longitude=11.7333,
            status="OPERATIONAL",
        )
        bharati = Station(
            id="bharati",
            name="Bharati Research Station",
            location="Larsemann Hills",
            latitude=-69.4072,
            longitude=76.1872,
            status="OPERATIONAL",
        )
        session.add_all([maitri, bharati])

        # Maitri Assets
        maitri_assets = [
            Asset(id="BLD-MAI-MAIN", station_id="maitri", name="Maitri Main Station Complex", type="BUILDING", status="RUNNING", health_score=0.96),
            Asset(id="GEN-MAI-001", station_id="maitri", name="Primary Diesel Generator 1", type="GENERATOR", status="RUNNING", health_score=0.94),
            Asset(id="GEN-MAI-002", station_id="maitri", name="Primary Diesel Generator 2", type="GENERATOR", status="RUNNING", health_score=0.91),
            Asset(id="GEN-MAI-003", station_id="maitri", name="Standby Emergency Generator 3", type="GENERATOR", status="STOPPED", health_score=1.00),
            Asset(id="BAT-MAI-001", station_id="maitri", name="Battery Energy Storage Bank A (BESS)", type="BATTERY", status="RUNNING", health_score=0.98),
            Asset(id="SWG-MAI-001", station_id="maitri", name="Central Microgrid Switchgear", type="SWITCHGEAR", status="RUNNING", health_score=0.99),
            Asset(id="FUL-MAI-001", station_id="maitri", name="Polar Diesel Storage Tank 01", type="FUEL_TANK", status="RUNNING", health_score=0.98),
            Asset(id="FUL-MAI-002", station_id="maitri", name="Polar Diesel Storage Tank 02", type="FUEL_TANK", status="RUNNING", health_score=0.99),
            Asset(id="PMP-MAI-FUEL", station_id="maitri", name="Fuel Transfer Pump Skid", type="PUMP", status="RUNNING", health_score=0.95),
            Asset(id="PMP-MAI-LAKE", station_id="maitri", name="Lake Priyadarshini Pump House", type="WATER", status="RUNNING", health_score=0.93),
            Asset(id="WTR-MAI-001", station_id="maitri", name="Priyadarshini Water Treatment Plant", type="WATER", status="RUNNING", health_score=0.94),
            Asset(id="AWS-MAI-001", station_id="maitri", name="Automatic Weather Station (AWS)", type="SCIENCE", status="RUNNING", health_score=0.99),
            Asset(id="COM-MAI-001", station_id="maitri", name="Ku-Band Satellite Ground Station Radome", type="COMMS", status="RUNNING", health_score=0.98),
            Asset(id="HVC-MAI-001", station_id="maitri", name="Central HVAC & Hydronic Loop", type="HVAC", status="RUNNING", health_score=0.88),
            Asset(id="HLP-MAI-001", station_id="maitri", name="Maitri Polar Helipad Deck", type="LOGISTICS", status="RUNNING", health_score=1.00),
        ]

        # Bharati Assets
        bharati_assets = [
            Asset(id="BLD-BHA-MAIN", station_id="bharati", name="Bharati Station Superstructure", type="BUILDING", status="RUNNING", health_score=0.98),
            Asset(id="GEN-BHA-001", station_id="bharati", name="Combined Heat & Power (CHP) Unit 1", type="GENERATOR", status="RUNNING", health_score=0.97),
            Asset(id="GEN-BHA-002", station_id="bharati", name="Combined Heat & Power (CHP) Unit 2", type="GENERATOR", status="RUNNING", health_score=0.94),
            Asset(id="BAT-BHA-001", station_id="bharati", name="Main High-Capacity BESS Array", type="BATTERY", status="RUNNING", health_score=0.99),
            Asset(id="SWG-BHA-001", station_id="bharati", name="Microgrid Synchronous Switchboard", type="SWITCHGEAR", status="RUNNING", health_score=0.99),
            Asset(id="FUL-BHA-001", station_id="bharati", name="Bulk Fuel Tank Battery", type="FUEL_TANK", status="RUNNING", health_score=0.98),
            Asset(id="PMP-BHA-SEA", station_id="bharati", name="Coastal Sea-Water Pump House", type="WATER", status="RUNNING", health_score=0.96),
            Asset(id="WTR-BHA-001", station_id="bharati", name="Reverse Osmosis (RO) Desalination Plant", type="WATER", status="RUNNING", health_score=0.96),
            Asset(id="COM-BHA-001", station_id="bharati", name="Dual Tracking Satcom Radomes", type="COMMS", status="RUNNING", health_score=1.00),
            Asset(id="HLP-BHA-001", station_id="bharati", name="Certified Aviation Helipad Platform", type="LOGISTICS", status="RUNNING", health_score=1.00),
        ]
        session.add_all(maitri_assets + bharati_assets)

        # Inventory Items
        inventory = [
            InventoryItem(station_id="maitri", name="Arctic High-Grade Diesel", category="FUEL", current_level=45000.0, unit="LITERS", reorder_threshold=15000.0),
            InventoryItem(station_id="maitri", name="Ration & Dry Food Reserves", category="FOOD", current_level=120.0, unit="DAYS", reorder_threshold=30.0),
            InventoryItem(station_id="maitri", name="Medical Trauma Kit & Supplies", category="MEDICAL", current_level=100.0, unit="PCT", reorder_threshold=40.0),
            InventoryItem(station_id="maitri", name="Generator Spare Filters & Belts", category="SPARE_PARTS", current_level=25.0, unit="UNITS", reorder_threshold=5.0),
            InventoryItem(station_id="bharati", name="Arctic High-Grade Diesel", category="FUEL", current_level=60000.0, unit="LITERS", reorder_threshold=20000.0),
            InventoryItem(station_id="bharati", name="Ration & Dry Food Reserves", category="FOOD", current_level=180.0, unit="DAYS", reorder_threshold=45.0),
            InventoryItem(station_id="bharati", name="Medical Trauma Kit & Supplies", category="MEDICAL", current_level=100.0, unit="PCT", reorder_threshold=40.0),
            InventoryItem(station_id="bharati", name="CHP Generator Spare Components", category="SPARE_PARTS", current_level=30.0, unit="UNITS", reorder_threshold=8.0),
        ]
        session.add_all(inventory)
        await session.commit()
        print("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
