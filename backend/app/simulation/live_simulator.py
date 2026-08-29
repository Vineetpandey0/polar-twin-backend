import asyncio
import math
import random
import logging
from datetime import datetime, timezone
from app.schemas.telemetry import TelemetryMessage
from app.services.ingestion_service import ingestion_service

logger = logging.getLogger("live_telemetry_simulator")


class LiveTelemetrySimulator:
    def __init__(self) -> None:
        self.is_running = False
        self.step_count = 0
        
        # State variables for smooth AR(1) autoregressive physics drift
        self.temp_maitri = -20.5
        self.temp_bharati = -15.2
        self.cabin_maitri = 21.8
        self.cabin_bharati = 22.1
        self.gen1_temp = 81.2
        self.gen2_temp = 82.5
        self.bess_soc_maitri = 94.5
        self.bess_soc_bharati = 96.2

    async def start(self) -> None:
        self.is_running = True
        logger.info("Real-Time Antarctic Telemetry Physics Engine started.")
        
        while self.is_running:
            try:
                self.step_count += 1
                now = datetime.now(timezone.utc)
                
                # Diurnal sun cycle based on UTC hour (Antarctic solar time drift)
                hour = (now.hour + 4) % 24
                diurnal = math.sin((hour - 6) * math.pi / 12)
                
                # Smooth AR(1) temperature drift (No erratic jumping)
                target_maitri = -20.0 + 3.0 * diurnal
                self.temp_maitri = 0.96 * self.temp_maitri + 0.04 * target_maitri + random.uniform(-0.1, 0.1)
                
                target_bharati = -14.5 + 2.5 * diurnal
                self.temp_bharati = 0.96 * self.temp_bharati + 0.04 * target_bharati + random.uniform(-0.08, 0.08)
                
                # Cabin temperatures with HVAC thermal equilibrium
                self.cabin_maitri = 21.8 + 0.2 * math.sin(self.step_count / 15) + random.uniform(-0.03, 0.03)
                self.cabin_bharati = 22.1 + 0.2 * math.cos(self.step_count / 15) + random.uniform(-0.03, 0.03)
                
                # Genset coolant temperatures
                self.gen1_temp = 81.5 + 1.5 * math.sin(self.step_count / 10) + random.uniform(-0.1, 0.1)
                self.gen2_temp = 82.8 + 1.2 * math.cos(self.step_count / 10) + random.uniform(-0.1, 0.1)

                # Microgrid Telemetry Payload List
                telemetries = [
                  # --- MAITRI TELEMETRY ---
                  TelemetryMessage(station_id="maitri", asset_id="ENV-MAITRI", sensor_id="SEN-ENV-MAI-TEMP", metric="ambient_temperature", value=round(self.temp_maitri, 1), unit="°C", timestamp=now),
                  TelemetryMessage(station_id="maitri", asset_id="ENV-MAITRI", sensor_id="SEN-ENV-MAI-WIND", metric="wind_speed", value=round(24.5 + 5.0 * math.sin(self.step_count / 8) + random.uniform(-1, 1), 1), unit="km/h", timestamp=now),
                  TelemetryMessage(station_id="maitri", asset_id="BLD-MAI-MAIN", sensor_id="SEN-BLD-MAI-TEMP", metric="cabin_temp", value=round(self.cabin_maitri, 1), unit="°C", timestamp=now),
                  TelemetryMessage(station_id="maitri", asset_id="BLD-MAI-MAIN", sensor_id="SEN-BLD-MAI-LOAD", metric="power_demand_kw", value=round(112.5 + 4.0 * math.sin(self.step_count / 6), 1), unit="kW", timestamp=now),
                  TelemetryMessage(station_id="maitri", asset_id="GEN-MAI-001", sensor_id="SEN-GEN1-TEMP", metric="temperature", value=round(self.gen1_temp, 1), unit="°C", timestamp=now),
                  TelemetryMessage(station_id="maitri", asset_id="GEN-MAI-001", sensor_id="SEN-GEN1-PWR", metric="electricalPower", value=round(92.4 + random.uniform(-1, 1), 1), unit="kW", timestamp=now),
                  TelemetryMessage(station_id="maitri", asset_id="GEN-MAI-001", sensor_id="SEN-GEN1-FUEL", metric="fuel_consumption", value=round(21.2 + random.uniform(-0.3, 0.3), 1), unit="L/h", timestamp=now),
                  TelemetryMessage(station_id="maitri", asset_id="BAT-MAI-001", sensor_id="SEN-BAT-MAI-SOC", metric="soc", value=round(self.bess_soc_maitri, 1), unit="%", timestamp=now),
                  TelemetryMessage(station_id="maitri", asset_id="BAT-MAI-001", sensor_id="SEN-BAT-MAI-VOLT", metric="voltage", value=round(408.0 + random.uniform(-0.5, 0.5), 1), unit="V", timestamp=now),
                  TelemetryMessage(station_id="maitri", asset_id="PMP-MAI-LAKE", sensor_id="SEN-PMP-MAI-FLOW", metric="intake_flow", value=round(160.0 + random.uniform(-2, 2), 1), unit="L/h", timestamp=now),
                  TelemetryMessage(station_id="maitri", asset_id="FUL-MAI-001", sensor_id="SEN-FUL-MAI-LVL", metric="fuel_level", value=78.5, unit="%", timestamp=now),
                  TelemetryMessage(station_id="maitri", asset_id="COM-MAI-001", sensor_id="SEN-COM-MAI-SIG", metric="signal_strength", value=98.5, unit="%", timestamp=now),

                  # --- BHARATI TELEMETRY ---
                  TelemetryMessage(station_id="bharati", asset_id="ENV-BHARATI", sensor_id="SEN-ENV-BHA-TEMP", metric="ambient_temperature", value=round(self.temp_bharati, 1), unit="°C", timestamp=now),
                  TelemetryMessage(station_id="bharati", asset_id="ENV-BHARATI", sensor_id="SEN-ENV-BHA-WIND", metric="wind_speed", value=round(34.1 + 6.0 * math.cos(self.step_count / 8) + random.uniform(-1, 1), 1), unit="km/h", timestamp=now),
                  TelemetryMessage(station_id="bharati", asset_id="BLD-BHA-MAIN", sensor_id="SEN-BLD-BHA-TEMP", metric="cabin_temp", value=round(self.cabin_bharati, 1), unit="°C", timestamp=now),
                  TelemetryMessage(station_id="bharati", asset_id="BLD-BHA-MAIN", sensor_id="SEN-BLD-BHA-LOAD", metric="totalBaseLoad", value=round(135.0 + 5.0 * math.sin(self.step_count / 5), 1), unit="kW", timestamp=now),
                  TelemetryMessage(station_id="bharati", asset_id="CHP-BHA-001", sensor_id="SEN-CHP1-TEMP", metric="temperature", value=round(self.gen2_temp, 1), unit="°C", timestamp=now),
                  TelemetryMessage(station_id="bharati", asset_id="CHP-BHA-001", sensor_id="SEN-CHP1-PWR", metric="electricalPower", value=round(134.5 + random.uniform(-1.5, 1.5), 1), unit="kW", timestamp=now),
                  TelemetryMessage(station_id="bharati", asset_id="CHP-BHA-001", sensor_id="SEN-CHP1-HEAT", metric="thermalOutput", value=round(164.0 + random.uniform(-2, 2), 1), unit="kW", timestamp=now),
                  TelemetryMessage(station_id="bharati", asset_id="BAT-BHA-001", sensor_id="SEN-BAT-BHA-SOC", metric="soc", value=round(self.bess_soc_bharati, 1), unit="%", timestamp=now),
                  TelemetryMessage(station_id="bharati", asset_id="BAT-BHA-001", sensor_id="SEN-BAT-BHA-VOLT", metric="busVoltage", value=round(412.0 + random.uniform(-0.5, 0.5), 1), unit="V", timestamp=now),
                  TelemetryMessage(station_id="bharati", asset_id="PMP-BHA-SEA", sensor_id="SEN-PMP-BHA-FLOW", metric="seawaterFlow", value=round(4250.0 + random.uniform(-30, 30), 1), unit="L/h", timestamp=now),
                  TelemetryMessage(station_id="bharati", asset_id="PMP-BHA-SEA", sensor_id="SEN-PMP-BHA-TEMP", metric="seawaterTemp", value=round(-1.2 + random.uniform(-0.1, 0.1), 1), unit="°C", timestamp=now),
                  TelemetryMessage(station_id="bharati", asset_id="FUL-BHA-001", sensor_id="SEN-FUL-BHA-LVL", metric="fuelLevel", value=75.0, unit="%", timestamp=now),
                  TelemetryMessage(station_id="bharati", asset_id="COM-BHA-AGEOS", sensor_id="SEN-COM-BHA-DOWN", metric="downlinkRate", value=105.0, unit="Mbps", timestamp=now),
                ]

                for msg in telemetries:
                    await ingestion_service.process(msg)

                import os
                sleep_interval = float(os.getenv("SIMULATION_INTERVAL_SECONDS", "600"))
                await asyncio.sleep(sleep_interval)
            except Exception as e:
                logger.error(f"Error in telemetry physics engine: {e}")
                await asyncio.sleep(10)

    def stop(self) -> None:
        self.is_running = False


live_telemetry_simulator = LiveTelemetrySimulator()
