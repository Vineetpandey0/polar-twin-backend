from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.core.config import settings

# Determine DB URL: Use settings.DATABASE_URL
db_url = settings.DATABASE_URL
if "postgresql+asyncpg://" not in db_url:
    if "postgresql://" in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    elif "postgres://" in db_url:
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://")

connect_args = {
    "statement_cache_size": 0,
    "timeout": 15,
}

print(f"[DB Engine] Connected to Database Target: {db_url.split('@')[-1] if '@' in db_url else db_url}")

engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
    pool_size=10,
    max_overflow=15,
    pool_recycle=300,
    pool_pre_ping=True,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    from app.models.base import Base
    from app.models.station import Station
    from app.models.asset import Asset
    import app.models.sensor_reading
    import app.models.alert
    import app.models.inventory
    import app.models.maintenance

    # 1. Create all database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. Seed default station and asset records into database if not present
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Station))
        existing_stations = result.scalars().all()
        if not existing_stations:
            maitri_st = Station(
                id="maitri",
                name="Maitri Research Station",
                location="Schirmacher Oasis, Queen Maud Land",
                latitude=-70.7667,
                longitude=11.7333,
                status="OPERATIONAL",
            )
            bharati_st = Station(
                id="bharati",
                name="Bharati Research Station",
                location="Larsemann Hills",
                latitude=-69.4072,
                longitude=76.1872,
                status="OPERATIONAL",
            )
            session.add_all([maitri_st, bharati_st])
            await session.commit()

            # Seed Maitri Assets
            maitri_assets = [
                ("BLD-MAI-MAIN", "Maitri Main Station Complex", "BUILDING"),
                ("GEN-MAI-001", "Primary Diesel Generator 1", "GENERATOR"),
                ("GEN-MAI-002", "Primary Diesel Generator 2", "GENERATOR"),
                ("GEN-MAI-003", "Standby Emergency Generator 3", "GENERATOR"),
                ("BAT-MAI-001", "Battery Energy Storage Bank A (BESS)", "BATTERY"),
                ("SWG-MAI-001", "Central Microgrid Switchgear", "SWITCHGEAR"),
                ("FUL-MAI-001", "Polar Diesel Storage Tank 01", "FUEL_TANK"),
                ("FUL-MAI-002", "Polar Diesel Storage Tank 02", "FUEL_TANK"),
                ("PMP-MAI-FUEL", "Fuel Transfer Pump Skid", "PUMP"),
                ("PMP-MAI-LAKE", "Lake Priyadarshini Pump House", "WATER"),
                ("WTR-MAI-001", "Priyadarshini Water Treatment Plant", "WATER"),
                ("AWS-MAI-001", "Automatic Weather Station (AWS)", "SCIENCE"),
                ("COM-MAI-001", "Ku-Band Satellite Ground Station Radome", "COMMS"),
                ("HVC-MAI-001", "Central HVAC & Hydronic Loop", "HVAC"),
                ("HLP-MAI-001", "Maitri Polar Helipad Deck", "LOGISTICS"),
            ]
            for aid, name, atype in maitri_assets:
                session.add(Asset(id=aid, station_id="maitri", name=name, type=atype, status="RUNNING", health_score=0.95))

            # Seed Bharati Assets
            bharati_assets = [
                ("BLD-BHA-MAIN", "Bharati Station Superstructure", "BUILDING"),
                ("CHP-BHA-001", "Combined Heat & Power (CHP) Unit 1", "GENERATOR"),
                ("CHP-BHA-002", "Combined Heat & Power (CHP) Unit 2", "GENERATOR"),
                ("BAT-BHA-001", "Main High-Capacity BESS Array", "BATTERY"),
                ("SWG-BHA-001", "Microgrid Synchronous Switchboard", "SWITCHGEAR"),
                ("FUL-BHA-001", "Bulk Fuel Tank Battery", "FUEL_TANK"),
                ("PMP-BHA-SEA", "Coastal Sea-Water Pump House", "WATER"),
                ("WTR-BHA-001", "Reverse Osmosis (RO) Desalination Plant", "WATER"),
                ("WWTP-BHA-001", "Wastewater Treatment Plant", "WATER"),
                ("COM-BHA-AGEOS", "ISRO AGEOS Dual Tracking Radomes", "COMMS"),
                ("HLP-BHA-001", "Certified Aviation Helipad Platform", "LOGISTICS"),
            ]
            for aid, name, atype in bharati_assets:
                session.add(Asset(id=aid, station_id="bharati", name=name, type=atype, status="RUNNING", health_score=0.98))

            await session.commit()

        # 3. Alerts check and seed
        from app.models.alert import Alert
        alert_res = await session.execute(select(Alert))
        if not alert_res.scalars().first():
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            session.add_all([
                Alert(station_id="maitri", asset_id="HVC-MAI-001", severity="WARNING", title="HVAC Thermal Load Delta Exceeded", message="Central HVAC heating load at 92% due to -25.2°C ambient blizzard conditions", reason="Intake duct air temperature dropped below -24°C, increasing auxiliary heating element duty cycle.", remedy="Inspect thermal intake dampers and enable secondary zone circulation fan.", acknowledged=False, created_at=now - timedelta(minutes=15)),
                Alert(station_id="maitri", asset_id="GEN-MAI-002", severity="WARNING", title="Primary Generator Coolant Temp Warning", message="GEN-MAI-002 coolant temperature operating at 82.1°C (Threshold: 80°C)", reason="Continuous 67 kW active load under restricted intake radiator airflow.", remedy="Clear snow accumulation around radiator intake louvers.", acknowledged=False, created_at=now - timedelta(minutes=48)),
                Alert(station_id="maitri", asset_id="COM-MAI-001", severity="WARNING", title="Ku-Band Tracking Servo Torque Advisory", message="Ku-Band Satellite Ground Station experiencing intermittent 45-knot wind gusts.", reason="Azimuth drive motor current elevated by 14% to maintain satellite lock.", remedy="Verify radome de-icing heating tape and monitor pedestal encoder.", acknowledged=False, created_at=now - timedelta(minutes=95)),
                Alert(station_id="maitri", asset_id="WTR-MAI-001", severity="INFO", title="Priyadarshini Water Unit Nominal Filtration", message="Daily meltwater filtration batch completed: 8,200 L reserve maintained.", reason="Thermal heating line operational, pump pressure stable at 3.8 bar.", remedy="Standard routine inspection on next scheduled cycle.", acknowledged=True, created_at=now - timedelta(hours=4), resolved_at=now - timedelta(hours=3)),
                Alert(station_id="maitri", asset_id="BAT-MAI-001", severity="INFO", title="BESS Microgrid Frequency Balancing Mode Active", message="Battery Energy Storage Bank A maintaining synchronous bus frequency at 50.02 Hz.", reason="Automatic inverter active power response nominal.", remedy="No manual operator intervention required.", acknowledged=True, created_at=now - timedelta(hours=8), resolved_at=now - timedelta(hours=7)),
                Alert(station_id="bharati", asset_id="CHP-BHA-001", severity="WARNING", title="CHP Thermal Recovery Exchanger Delta", message="Heat exchanger differential pressure +12% above seasonal baseline.", reason="Soot accumulation on primary exhaust gas bypass baffle.", remedy="Schedule routine heat exchanger tube bundle soot blow cycle.", acknowledged=False, created_at=now - timedelta(minutes=32)),
                Alert(station_id="bharati", asset_id="WTR-BHA-001", severity="WARNING", title="Desalination Reverse Osmosis Membrane Flux Warning", message="RO Permeate flux reduced to 14.2 L/h-m² due to cold coastal brine.", reason="Seawater temperature at intake reached -1.8°C supercooled state.", remedy="Increase intake pre-heat loop flow and verify high-pressure pump inlet pressure.", acknowledged=False, created_at=now - timedelta(minutes=72)),
                Alert(station_id="bharati", asset_id="BAT-BHA-001", severity="INFO", title="Battery Storage Bank Floating Charge Mode", message="Main Energy Storage Bank reached 94% SOC. Switch to float charging.", reason="CHP Generator output surplus currently balancing base load.", remedy="No action required. Automatic BESS BMS power management active.", acknowledged=True, created_at=now - timedelta(hours=2), resolved_at=now - timedelta(hours=1, minutes=30)),
                Alert(station_id="bharati", asset_id="COM-BHA-AGEOS", severity="INFO", title="ISRO AGEOS Telemetry Tracking Pass Nominal", message="Oceansat-3 remote sensing polar pass acquired at 18.5 dB SNR.", reason="Clear atmospheric conditions and optimum elevation angle (64°).", remedy="Raw telemetry stream archived to local storage array.", acknowledged=True, created_at=now - timedelta(hours=5), resolved_at=now - timedelta(hours=4, minutes=45)),
                Alert(station_id="bharati", asset_id="SWG-BHA-001", severity="INFO", title="Synchronous Switchboard Bus Tie Redundancy Verified", message="Weekly automated interlock and breaker health self-test passed.", reason="Zero trip signals detected across 400V 3-phase feeder banks.", remedy="Log telemetry verification in monthly NCPOR electrical log.", acknowledged=True, created_at=now - timedelta(hours=12), resolved_at=now - timedelta(hours=11)),
            ])
            await session.commit()

        # 4. Inventory check and seed
        from app.models.inventory import InventoryItem
        inv_res = await session.execute(select(InventoryItem))
        if not inv_res.scalars().first():
            session.add_all([
                InventoryItem(station_id="maitri", name="Arctic High-Grade Polar Diesel", category="FUEL", current_level=45000.0, max_capacity=65000.0, unit="LITERS", reorder_threshold=15000.0, burn_rate_daily=375.0),
                InventoryItem(station_id="maitri", name="Freeze-Dried & Ration Reserves", category="FOOD", current_level=120.0, max_capacity=180.0, unit="DAYS", reorder_threshold=30.0, burn_rate_daily=1.0),
                InventoryItem(station_id="maitri", name="Medical Trauma & Surgical Stock", category="MEDICAL", current_level=95.0, max_capacity=100.0, unit="PCT", reorder_threshold=40.0, burn_rate_daily=0.2),
                InventoryItem(station_id="maitri", name="Generator Fuel Injectors & Belts", category="SPARE_PARTS", current_level=25.0, max_capacity=35.0, unit="UNITS", reorder_threshold=5.0, burn_rate_daily=0.1),
                InventoryItem(station_id="maitri", name="Aviation Turbine Fuel (Jet A-1)", category="FUEL", current_level=18500.0, max_capacity=25000.0, unit="LITERS", reorder_threshold=6000.0, burn_rate_daily=95.0),
                InventoryItem(station_id="maitri", name="Reverse Osmosis Filter Cartridges", category="SPARE_PARTS", current_level=16.0, max_capacity=24.0, unit="UNITS", reorder_threshold=4.0, burn_rate_daily=0.05),
                InventoryItem(station_id="bharati", name="Arctic High-Grade Polar Diesel", category="FUEL", current_level=60000.0, max_capacity=80000.0, unit="LITERS", reorder_threshold=20000.0, burn_rate_daily=330.0),
                InventoryItem(station_id="bharati", name="Freeze-Dried & Ration Reserves", category="FOOD", current_level=180.0, max_capacity=240.0, unit="DAYS", reorder_threshold=45.0, burn_rate_daily=1.0),
                InventoryItem(station_id="bharati", name="Medical Trauma Kits & Emergency O2", category="MEDICAL", current_level=100.0, max_capacity=100.0, unit="PCT", reorder_threshold=40.0, burn_rate_daily=0.1),
                InventoryItem(station_id="bharati", name="CHP Turbine Filters & Seals", category="SPARE_PARTS", current_level=30.0, max_capacity=40.0, unit="UNITS", reorder_threshold=8.0, burn_rate_daily=0.1),
                InventoryItem(station_id="bharati", name="Synthetic Arctic Engine Lubricant 5W-40", category="FUEL", current_level=2400.0, max_capacity=3500.0, unit="LITERS", reorder_threshold=800.0, burn_rate_daily=12.0),
                InventoryItem(station_id="bharati", name="Radome Azimuth Bearings & Slip Rings", category="SPARE_PARTS", current_level=8.0, max_capacity=12.0, unit="UNITS", reorder_threshold=2.0, burn_rate_daily=0.02),
            ])
            await session.commit()

        # 5. Maintenance records check and seed
        from app.models.maintenance import MaintenanceRecord
        maint_res = await session.execute(select(MaintenanceRecord))
        if not maint_res.scalars().first():
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            session.add_all([
                MaintenanceRecord(asset_id="GEN-MAI-001", title="500-Hour Primary Generator Overhaul", description="Replace lubricating oil filter, inspect injector nozzles, check turbocharger play and dynamic governor calibration.", priority="HIGH", status="PENDING", scheduled_date=now + timedelta(days=5)),
                MaintenanceRecord(asset_id="HVC-MAI-001", title="Hydronic Heating Loop Glycol Concentration Test", description="Verify ethylene glycol/water ratio at 60/40 for -45°C freeze protection and flush air vent valves.", priority="MEDIUM", status="COMPLETED", scheduled_date=now - timedelta(days=2), completed_at=now - timedelta(days=2)),
                MaintenanceRecord(asset_id="WTR-MAI-001", title="Priyadarshini Lake Submerged Pump Inspection", description="De-ice pump intake cradle, test backup heating element resistance, and calibrate pressure transducer.", priority="MEDIUM", status="PENDING", scheduled_date=now + timedelta(days=12)),
                MaintenanceRecord(asset_id="COM-MAI-001", title="Ku-Band Radome Blower & De-icer Check", description="Verify blower centrifugal fan bearing noise and inspect RF window seal integrity under polar wind.", priority="LOW", status="PENDING", scheduled_date=now + timedelta(days=18)),
                MaintenanceRecord(asset_id="CHP-BHA-001", title="CHP Thermal Exchanger De-sooting Cycle", description="Clean exhaust heat recovery bundle tubes, inspect pneumatic bypass damper actuators, and verify thermal output.", priority="HIGH", status="IN_PROGRESS", scheduled_date=now + timedelta(days=1)),
                MaintenanceRecord(asset_id="BAT-BHA-001", title="BESS Lithium Iron Phosphate Cell Impedance Audit", description="Measure AC internal resistance on all 120 cell modules, check active BMS equalizer balances and busbar torques.", priority="MEDIUM", status="PENDING", scheduled_date=now + timedelta(days=8)),
                MaintenanceRecord(asset_id="COM-BHA-AGEOS", title="AGEOS Dual Radome Azimuth Gearbox Lubrication", description="Re-pack low-temperature synthetic grease in main azimuth slew bearing and inspect counterweight linkages.", priority="LOW", status="COMPLETED", scheduled_date=now - timedelta(days=7), completed_at=now - timedelta(days=7)),
                MaintenanceRecord(asset_id="WTR-BHA-001", title="Reverse Osmosis Membrane Chemical Clean (CIP)", description="Perform acid/alkaline CIP flush on RO elements to restore specific permeate flux rate.", priority="MEDIUM", status="PENDING", scheduled_date=now + timedelta(days=15)),
            ])
            await session.commit()

