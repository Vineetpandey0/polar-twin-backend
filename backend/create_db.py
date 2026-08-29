import sys
import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.base import Base
from app.models.station import Station
from app.models.asset import Asset
import app.models.sensor_reading
import app.models.alert
import app.models.inventory
import app.models.maintenance

def create_and_seed_tables():
    db_url = settings.DATABASE_URL
    print(f"Connecting to database: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    
    # Convert async driver string to standard sync driver string
    if "+asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "")
    elif "+aiosqlite" in db_url:
        db_url = db_url.replace("+aiosqlite", "")

    # For postgresql, fallback to psycopg2
    engine = create_engine(db_url, echo=True)

    print("\n[1/2] Creating all database tables (stations, assets, sensor_readings, alerts, inventory_items, maintenance_records)...")
    Base.metadata.create_all(engine)
    print("[OK] All database tables created successfully!")

    print("\n[2/2] Seeding initial stations and assets into database...")
    SessionLocal = sessionmaker(bind=engine)

    with SessionLocal() as session:
        result = session.execute(select(Station))
        existing = result.scalars().all()
        
        if not existing:
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
            session.commit()

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

            session.commit()
            print("[OK] Station and asset records seeded successfully!")
        else:
            print(f"[OK] Found {len(existing)} existing stations in database.")

    engine.dispose()
    print("\nDatabase initialization complete! All tables are active.")

if __name__ == "__main__":
    create_and_seed_tables()
