import asyncio
import math
import logging
from datetime import datetime, timezone
from app.schemas.telemetry import TelemetryMessage
from app.services.ingestion_service import ingestion_service

logger = logging.getLogger("live_telemetry_simulator")


class LiveTelemetrySimulator:
    """
    Physically-grounded Antarctic Microgrid & Environmental Simulator.
    Models interconnected thermodynamic, mechanical, and electrical subsystems:
      - Solar Diurnal Cycle drives Ambient Temperature (with thermal inertia).
      - Polar thermal gradient drives Katabatic Wind Speed.
      - Ambient conditions govern Building Convective Heat Loss & Cabin Temperature.
      - Building Heat Loss determines Station Electrical/Thermal Demand.
      - Generator Electrical Load directly drives:
          * Engine Coolant Temperature (Thermodynamic heat rejection curve)
          * Governor Speed-Droop (Synchronous 1500 RPM droop curve)
          * Mechanical Vibration (Torque imbalance & speed deviation)
          * Specific Fuel Consumption Rate (BSFC diesel curve)
          * Fuel Tank Level (Integrated continuous depletion)
      - Combined Heat & Power (CHP at Bharati) co-generates electricity & thermal output in stoichiometric ratio.
      - Battery Storage System (BESS) acts as electrical buffer; Bus Voltage & Temp track State of Charge (SOC).
      - Pumping & Hydraulic stations scale with water temperature, cooling, and viscosity.
    """

    def __init__(self) -> None:
        self.is_running = False
        self.step_count = 0

        # Continuous state variables for physical continuity across ticks
        # Maitri State
        self.temp_maitri = -20.8          # °C
        self.wind_maitri = 26.5          # km/h
        self.cabin_maitri = 21.9         # °C
        self.bess_soc_maitri = 94.2      # %
        self.fuel_level_maitri = 78.5    # %

        # Bharati State
        self.temp_bharati = -14.6         # °C
        self.wind_bharati = 32.4         # km/h
        self.cabin_bharati = 22.0        # °C
        self.bess_soc_bharati = 95.8     # %
        self.fuel_level_bharati = 75.0   # %

    async def start(self) -> None:
        self.is_running = True
        logger.info("Real-Time Antarctic Interconnected Physics Engine started.")

        while self.is_running:
            try:
                self.step_count += 1
                now = datetime.now(timezone.utc)

                # ── 1. SOLAR DIURNAL CYCLE (UTC HOUR DRIVEN) ─────────────────
                # Solar angle varies with 24-hour cycle; peak solar warming around 14:00 local time
                hour = (now.hour + 4) % 24
                diurnal = math.sin((hour - 5) * math.pi / 12)

                # ── 2. MAITRI INTERCONNECTED SYSTEM (INLAND OASIS MICROGRID) ──
                # Ambient Temperature with thermal inertia (continuous, no random jumping)
                target_temp_mai = -21.0 + 3.8 * diurnal
                self.temp_maitri = round(0.92 * self.temp_maitri + 0.08 * target_temp_mai, 2)

                # Katabatic Wind Speed: Cold dense polar air sinking accelerates wind
                # Negative temp delta increases wind velocity
                cold_density_factor = (-15.0 - self.temp_maitri) / 10.0
                target_wind_mai = 20.0 + 7.5 * cold_density_factor + 3.0 * math.cos(self.step_count * 0.1)
                self.wind_maitri = round(0.90 * self.wind_maitri + 0.10 * target_wind_mai, 1)

                # Building Convective Skin Heat Loss
                wind_convective_factor = 1.0 + 0.018 * max(0.0, self.wind_maitri - 20.0)
                thermal_loss_mai = 0.88 * (22.0 - self.temp_maitri) * wind_convective_factor

                # Station Power Demand: Base electrical load + HVAC heating load
                base_load_mai = 74.0
                heating_load_mai = 0.92 * thermal_loss_mai
                total_power_demand_mai = round(base_load_mai + heating_load_mai, 1)  # kW

                # Cabin Temperature: Governed by HVAC heating compensation
                hvac_correction = (heating_load_mai / 0.92) - thermal_loss_mai
                target_cabin_mai = 22.0 + 0.03 * hvac_correction
                self.cabin_maitri = round(0.95 * self.cabin_maitri + 0.05 * target_cabin_mai, 2)

                # Generator 1: Supplies station demand while balancing BESS
                gen1_power = round(total_power_demand_mai * 0.88, 1)  # kW

                # Generator Governor Droop Curve: Synchronous speed is 1500 RPM at 90 kW
                # Under heavier load, engine droop drops speed slightly (ISO 8528 droop physics)
                gen1_rpm = round(1500.0 - 0.075 * (gen1_power - 90.0), 1)

                # Engine Coolant Temperature: Directly tracks generator electrical output (heat rejection)
                # Counterbalanced slightly by ambient radiator airflow
                gen1_temp = round(77.5 + 0.092 * gen1_power - 0.025 * (self.temp_maitri + 20.0), 1)  # °C

                # Mechanical Engine Vibration: Proportional to torque load and RPM deviation
                gen1_vibration = round(1.75 + 0.011 * gen1_power + 0.035 * abs(gen1_rpm - 1500.0), 2)  # mm/s

                # Fuel Consumption Rate (BSFC diesel curve): Directly scales with electrical power
                gen1_fuel_rate = round(4.5 + 0.182 * gen1_power, 2)  # L/h

                # Fuel Storage Tank Level: Integrated fuel consumption over time
                # In 10 minutes (0.1667 h), a 15,000 L bulk tank decreases by (fuel_rate * 0.1667 / 15000) * 100%
                fuel_consumed_fraction = (gen1_fuel_rate * 0.1667 / 15000.0) * 100.0
                self.fuel_level_maitri = max(15.0, round(self.fuel_level_maitri - fuel_consumed_fraction, 3))

                # Battery Storage (BESS): Peak shave & frequency support
                bess_power_mai = round(total_power_demand_mai - gen1_power, 1)  # Positive = discharging
                # Update SOC
                soc_delta_mai = -(bess_power_mai * 0.1667 / 250.0) * 100.0  # 250 kWh capacity bank
                self.bess_soc_maitri = max(20.0, min(99.0, round(self.bess_soc_maitri + soc_delta_mai, 2)))
                # Bus Voltage: Direct electrochemical open-circuit voltage function of SOC
                gen1_bus_voltage = round(394.0 + 0.36 * self.bess_soc_maitri - 0.08 * (bess_power_mai / 10.0), 1)

                # Lake Pump: Flow inversely proportional to freezing viscosity
                lake_pump_flow = round(162.0 + 1.1 * (self.temp_maitri + 20.0), 1)  # L/h

                # Satellite Comms: Signal attenuation coupled to wind turbulence & ice drift
                signal_maitri = max(82.0, round(99.4 - 0.07 * max(0.0, self.wind_maitri - 20.0), 1))

                # ── 3. BHARATI INTERCONNECTED SYSTEM (COASTAL CHP MICROGRID) ──
                # Coastal Larsemann Hills ambient temperature
                target_temp_bha = -14.8 + 3.2 * diurnal
                self.temp_bharati = round(0.92 * self.temp_bharati + 0.08 * target_temp_bha, 2)

                # Coastal Winds
                target_wind_bha = 28.0 + 6.0 * ((-10.0 - self.temp_bharati) / 8.0) + 4.0 * math.sin(self.step_count * 0.12)
                self.wind_bharati = round(0.90 * self.wind_bharati + 0.10 * target_wind_bha, 1)

                # Bharati Superstructure Heat Loss
                bha_wind_factor = 1.0 + 0.015 * max(0.0, self.wind_bharati - 25.0)
                thermal_loss_bha = 0.95 * (22.0 - self.temp_bharati) * bha_wind_factor

                # Base station load + heating demand
                total_power_demand_bha = round(92.0 + 0.90 * thermal_loss_bha, 1)  # kW

                # Cabin Temperature (Triple-glazed insulated aerodynamic pod)
                target_cabin_bha = 22.1 - 0.015 * (thermal_loss_bha - 35.0)
                self.cabin_bharati = round(0.95 * self.cabin_bharati + 0.05 * target_cabin_bha, 2)

                # CHP Unit 1: Combined Heat & Power
                chp1_power = round(total_power_demand_bha * 0.90, 1)  # kW

                # Governor Droop for CHP alternator (1500 RPM synchronous speed)
                chp1_rpm = round(1500.0 - 0.065 * (chp1_power - 120.0), 1)

                # CHP Thermal Output: Stoichiometric heat recovery directly coupled to electrical kW!
                # Thermal efficiency yields approx 1.22x electrical power in heat recovery
                chp1_thermal = round(1.22 * chp1_power + 0.5 * (20.0 - self.temp_bharati) * 0.1, 1)  # kWth

                # CHP Coolant Temperature: Direct heat balance of combustion & thermal recovery
                chp1_temp = round(79.0 + 0.085 * chp1_power - 0.02 * (self.temp_bharati + 15.0), 1)  # °C

                # Mechanical Vibration
                chp1_vibration = round(1.90 + 0.009 * chp1_power + 0.03 * abs(chp1_rpm - 1500.0), 2)

                # Fuel Storage Depletion
                chp1_fuel_rate = 5.2 + 0.19 * chp1_power  # L/h
                fuel_consumed_bha = (chp1_fuel_rate * 0.1667 / 20000.0) * 100.0
                self.fuel_level_bharati = max(15.0, round(self.fuel_level_bharati - fuel_consumed_bha, 3))

                # Bharati High-Capacity BESS Array
                bess_power_bha = round(total_power_demand_bha - chp1_power, 1)
                soc_delta_bha = -(bess_power_bha * 0.1667 / 400.0) * 100.0
                self.bess_soc_bharati = max(20.0, min(99.0, round(self.bess_soc_bharati + soc_delta_bha, 2)))
                chp1_bus_voltage = round(396.0 + 0.38 * self.bess_soc_bharati - 0.05 * (bess_power_bha / 10.0), 1)

                # Seawater Heat Exchanger & Desalination Pump: Flow rate scales with CHP heat rejection
                seawater_flow = round(3850.0 + 3.4 * chp1_power, 1)  # L/h
                seawater_temp = round(-1.4 + 0.03 * (self.temp_bharati + 15.0), 2)  # °C

                # ISRO AGEOS Satellite Tracking Station Downlink
                comms_attenuation = max(0.0, self.wind_bharati - 30.0) * 0.25
                downlink_rate = max(45.0, round(105.0 - comms_attenuation, 1))  # Mbps

                # ── 4. COMPILE AND BROADCAST TELEMETRY PAYLOADS ───────────────
                telemetries = [
                    # --- MAITRI ASSET TELEMETRY ---
                    TelemetryMessage(station_id="maitri", asset_id="ENV-MAITRI", sensor_id="SEN-ENV-MAI-TEMP", metric="ambient_temperature", value=self.temp_maitri, unit="°C", timestamp=now),
                    TelemetryMessage(station_id="maitri", asset_id="ENV-MAITRI", sensor_id="SEN-ENV-MAI-WIND", metric="wind_speed", value=self.wind_maitri, unit="km/h", timestamp=now),
                    TelemetryMessage(station_id="maitri", asset_id="BLD-MAI-MAIN", sensor_id="SEN-BLD-MAI-TEMP", metric="cabin_temp", value=self.cabin_maitri, unit="°C", timestamp=now),
                    TelemetryMessage(station_id="maitri", asset_id="BLD-MAI-MAIN", sensor_id="SEN-BLD-MAI-LOAD", metric="power_demand_kw", value=total_power_demand_mai, unit="kW", timestamp=now),
                    TelemetryMessage(station_id="maitri", asset_id="GEN-MAI-001", sensor_id="SEN-GEN1-TEMP", metric="temperature", value=gen1_temp, unit="°C", timestamp=now),
                    TelemetryMessage(station_id="maitri", asset_id="GEN-MAI-001", sensor_id="SEN-GEN1-PWR", metric="electricalPower", value=gen1_power, unit="kW", timestamp=now),
                    TelemetryMessage(station_id="maitri", asset_id="GEN-MAI-001", sensor_id="SEN-GEN1-FUEL", metric="fuel_consumption", value=round(gen1_fuel_rate, 1), unit="L/h", timestamp=now),
                    TelemetryMessage(station_id="maitri", asset_id="GEN-MAI-001", sensor_id="SEN-GEN1-RPM", metric="rpm", value=gen1_rpm, unit="RPM", timestamp=now),
                    TelemetryMessage(station_id="maitri", asset_id="GEN-MAI-001", sensor_id="SEN-GEN1-VIB", metric="vibration", value=gen1_vibration, unit="mm/s", timestamp=now),
                    TelemetryMessage(station_id="maitri", asset_id="BAT-MAI-001", sensor_id="SEN-BAT-MAI-SOC", metric="soc", value=round(self.bess_soc_maitri, 1), unit="%", timestamp=now),
                    TelemetryMessage(station_id="maitri", asset_id="BAT-MAI-001", sensor_id="SEN-BAT-MAI-VOLT", metric="voltage", value=gen1_bus_voltage, unit="V", timestamp=now),
                    TelemetryMessage(station_id="maitri", asset_id="PMP-MAI-LAKE", sensor_id="SEN-PMP-MAI-FLOW", metric="intake_flow", value=lake_pump_flow, unit="L/h", timestamp=now),
                    TelemetryMessage(station_id="maitri", asset_id="FUL-MAI-001", sensor_id="SEN-FUL-MAI-LVL", metric="fuel_level", value=round(self.fuel_level_maitri, 1), unit="%", timestamp=now),
                    TelemetryMessage(station_id="maitri", asset_id="COM-MAI-001", sensor_id="SEN-COM-MAI-SIG", metric="signal_strength", value=signal_maitri, unit="%", timestamp=now),

                    # --- BHARATI ASSET TELEMETRY ---
                    TelemetryMessage(station_id="bharati", asset_id="ENV-BHARATI", sensor_id="SEN-ENV-BHA-TEMP", metric="ambient_temperature", value=self.temp_bharati, unit="°C", timestamp=now),
                    TelemetryMessage(station_id="bharati", asset_id="ENV-BHARATI", sensor_id="SEN-ENV-BHA-WIND", metric="wind_speed", value=self.wind_bharati, unit="km/h", timestamp=now),
                    TelemetryMessage(station_id="bharati", asset_id="BLD-BHA-MAIN", sensor_id="SEN-BLD-BHA-TEMP", metric="cabin_temp", value=self.cabin_bharati, unit="°C", timestamp=now),
                    TelemetryMessage(station_id="bharati", asset_id="BLD-BHA-MAIN", sensor_id="SEN-BLD-BHA-LOAD", metric="totalBaseLoad", value=total_power_demand_bha, unit="kW", timestamp=now),
                    TelemetryMessage(station_id="bharati", asset_id="CHP-BHA-001", sensor_id="SEN-CHP1-TEMP", metric="temperature", value=chp1_temp, unit="°C", timestamp=now),
                    TelemetryMessage(station_id="bharati", asset_id="CHP-BHA-001", sensor_id="SEN-CHP1-PWR", metric="electricalPower", value=chp1_power, unit="kW", timestamp=now),
                    TelemetryMessage(station_id="bharati", asset_id="CHP-BHA-001", sensor_id="SEN-CHP1-HEAT", metric="thermalOutput", value=chp1_thermal, unit="kW", timestamp=now),
                    TelemetryMessage(station_id="bharati", asset_id="CHP-BHA-001", sensor_id="SEN-CHP1-RPM", metric="rpm", value=chp1_rpm, unit="RPM", timestamp=now),
                    TelemetryMessage(station_id="bharati", asset_id="CHP-BHA-001", sensor_id="SEN-CHP1-VIB", metric="vibration", value=chp1_vibration, unit="mm/s", timestamp=now),
                    TelemetryMessage(station_id="bharati", asset_id="BAT-BHA-001", sensor_id="SEN-BAT-BHA-SOC", metric="soc", value=round(self.bess_soc_bharati, 1), unit="%", timestamp=now),
                    TelemetryMessage(station_id="bharati", asset_id="BAT-BHA-001", sensor_id="SEN-BAT-BHA-VOLT", metric="busVoltage", value=chp1_bus_voltage, unit="V", timestamp=now),
                    TelemetryMessage(station_id="bharati", asset_id="PMP-BHA-SEA", sensor_id="SEN-PMP-BHA-FLOW", metric="seawaterFlow", value=seawater_flow, unit="L/h", timestamp=now),
                    TelemetryMessage(station_id="bharati", asset_id="PMP-BHA-SEA", sensor_id="SEN-PMP-BHA-TEMP", metric="seawaterTemp", value=seawater_temp, unit="°C", timestamp=now),
                    TelemetryMessage(station_id="bharati", asset_id="FUL-BHA-001", sensor_id="SEN-FUL-BHA-LVL", metric="fuelLevel", value=round(self.fuel_level_bharati, 1), unit="%", timestamp=now),
                    TelemetryMessage(station_id="bharati", asset_id="COM-BHA-AGEOS", sensor_id="SEN-COM-BHA-DOWN", metric="downlinkRate", value=downlink_rate, unit="Mbps", timestamp=now),
                ]

                for msg in telemetries:
                    await ingestion_service.process(msg)

                from app.core.config import settings
                sleep_interval = float(getattr(settings, "SIMULATION_INTERVAL_SECONDS", 600.0))
                await asyncio.sleep(sleep_interval)
            except Exception as e:
                logger.error(f"Error in telemetry physics engine: {e}", exc_info=True)
                from app.core.config import settings
                error_sleep = float(getattr(settings, "SIMULATION_INTERVAL_SECONDS", 600.0))
                await asyncio.sleep(error_sleep)

    def stop(self) -> None:
        self.is_running = False


live_telemetry_simulator = LiveTelemetrySimulator()
