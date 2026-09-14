import copy
import math
import logging
from typing import Dict, Any, List, Optional

from app.digital_twin.engine import digital_twin_engine
from app.analytics.anomaly_detector import anomaly_detector
from app.analytics.energy_forecaster import energy_forecaster

logger = logging.getLogger("scenario_engine")


class ScenarioEngine:
    """
    Advanced Multi-Variable Cascading Physics & ML-Driven Contingency Engine
    for Maitri and Bharati Antarctic Research Stations.
    """

    def __init__(self):
        self.available_scenarios = [
            {
                "id": "generator_thermal_runaway",
                "name": "Generator Thermal Runaway & Mechanical Degradation",
                "category": "POWER & MECHANICAL",
                "description": "Coolant and oil temperature surge causes governor throttling, RPM collapse, severe mechanical vibration, and microgrid power deficit.",
                "primary_asset": "GEN",
            },
            {
                "id": "generator_trip_blackout",
                "name": "Catastrophic Primary Generator Trip & Microgrid Cascade",
                "category": "POWER & MICROGRID",
                "description": "Sudden total failure of Primary Generator 1 triggers immediate BESS high-drain discharge, switchgear load shedding, and emergency auto-crank.",
                "primary_asset": "GEN",
            },
            {
                "id": "polar_blizzard_thermal_stress",
                "name": "Super-Blizzard & Life Support Thermal Stress",
                "category": "ENVIRONMENTAL & HVAC",
                "description": "-45°C ambient blizzard with 95 km/h winds cools hydronic loop, surges HVAC electric heating elements, and spikes fuel consumption +38%.",
                "primary_asset": "HVC",
            },
            {
                "id": "fuel_gelling_viscosity_loss",
                "name": "Polar Diesel Gelling & Fuel Rail Starvation",
                "category": "LOGISTICS & FUEL",
                "description": "Cold fuel gelling chokes transfer filters, dropping pump pressure and inducing erratic engine RPM hunting and power oscillation.",
                "primary_asset": "FUL",
            },
            {
                "id": "satellite_radome_servo_overload",
                "name": "Radome Azimuth Servo Slip & Ground Blackout",
                "category": "COMMUNICATIONS",
                "description": "Severe wind shear slips antenna azimuth drive pedestal, causing 3.8° pointing error, signal loss, and autonomous local buffering.",
                "primary_asset": "COM",
            },
            {
                "id": "water_intake_freeze_drought",
                "name": "Water Intake Freeze-Up & Life Support Drought",
                "category": "LIFE SUPPORT & WATER",
                "description": "Intake trace heating circuit fault freezes pipeline, tripping filtration pumps and triggering emergency potable water rationing.",
                "primary_asset": "WTR",
            },
        ]

    def get_catalog(self) -> List[Dict[str, Any]]:
        return self.available_scenarios

    def run_scenario(
        self,
        station_id: str,
        scenario_name: str,
        custom_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        st_id = station_id.lower()
        current_state = digital_twin_engine.get_station_state(st_id)
        if not current_state:
            # Fallback mock baseline if engine uninitialized
            current_state = {
                "station_id": st_id,
                "station_health_score": 0.94 if st_id == "maitri" else 0.98,
                "active_power_kw": 145.2 if st_id == "maitri" else 182.0,
                "total_fuel_burn_l_hr": 15.6 if st_id == "maitri" else 13.8,
                "connectivity_status": "LIVE",
                "assets": {},
            }

        projected_state = copy.deepcopy(current_state)
        assets = projected_state.get("assets", {})

        is_maitri = st_id == "maitri"
        gen_primary_id = "GEN-MAI-001" if is_maitri else "CHP-BHA-001"
        bess_id = "BAT-MAI-001" if is_maitri else "BAT-BHA-001"
        hvac_id = "HVC-MAI-001" if is_maitri else "BLD-BHA-MAIN"
        comms_id = "COM-MAI-001" if is_maitri else "COM-BHA-AGEOS"
        water_id = "WTR-MAI-001" if is_maitri else "WTR-BHA-001"

        custom_params = custom_params or {}

        # Default multi-variable telemetry state baseline
        gen_temp = 78.0
        gen_rpm = 1500.0
        gen_vib = 2.4
        gen_kw = 68.0 if is_maitri else 85.0
        bess_soc = 88.0 if is_maitri else 94.0
        bess_temp = 21.5
        bess_discharge_a = 12.0
        hvac_flow = 85.0
        hvac_power_kw = 42.0
        fuel_burn_daily = 375.0 if is_maitri else 330.0
        comms_signal = 98.0
        water_flow = 160.0
        ambient_temp = -25.0

        cascading_effects = []
        sop_steps = []
        scenario_key = scenario_name.lower()

        # -------------------------------------------------------------
        # 1. SCENARIO: Generator Thermal Runaway
        # -------------------------------------------------------------
        if scenario_key in ["generator_thermal_runaway", "generator_failure"]:
            temp_delta = float(custom_params.get("temp_delta", 18.5))
            gen_temp += temp_delta

            # Physics Coupling 1: Thermal -> Governor RPM Throttling
            # Higher heat decreases oil film thickness; governor pulls rack to prevent piston seizure
            rpm_drop = round(temp_delta * 8.65, 1)
            gen_rpm -= rpm_drop

            # Physics Coupling 2: RPM drop & Thermal Expansion -> Mechanical Vibration Surge
            # Cylinder misfire and harmonic imbalance
            vib_rise = round(temp_delta * 0.26 + (rpm_drop / 50.0), 2)
            gen_vib += vib_rise

            # Physics Coupling 3: Reduced RPM & Efficiency -> Power Generation Loss
            kw_loss = round((rpm_drop / 1500.0) * gen_kw * 1.35, 1)
            gen_kw = max(20.0, gen_kw - kw_loss)

            # Physics Coupling 4: Power Deficit -> BESS Discharge Acceleration
            # Microgrid deficit forces Battery Bank to dump current to sustain critical life-support
            bess_discharge_a += round(kw_loss * 2.1, 1)
            bess_temp += round(temp_delta * 0.32, 1)
            bess_soc -= 24.0 # Projected SOC loss over observation window

            projected_state["station_health_score"] = 0.61
            projected_state["active_power_kw"] = round(projected_state.get("active_power_kw", 145.0) - kw_loss, 1)

            if gen_primary_id in assets:
                assets[gen_primary_id]["health_score"] = 0.35
                assets[gen_primary_id]["operational_status"] = "DEGRADED"
                assets[gen_primary_id].setdefault("sensor_readings", {})["temperature"] = round(gen_temp, 1)
                assets[gen_primary_id]["sensor_readings"]["rpm"] = round(gen_rpm, 1)
                assets[gen_primary_id]["sensor_readings"]["vibration"] = round(gen_vib, 2)
                assets[gen_primary_id]["sensor_readings"]["power"] = round(gen_kw, 1)

            cascading_effects = [
                {
                    "stage": "PRIMARY TRIGGER",
                    "subsystem": "Diesel Engine Thermal Loop",
                    "parameter": "Coolant & Lubricating Oil Temperature",
                    "nominal": 78.0,
                    "projected": round(gen_temp, 1),
                    "unit": "°C",
                    "delta": f"+{temp_delta}°C",
                    "mechanism": "Radiator fan clutch slip and high continuous electrical load causes cooling loop saturation.",
                },
                {
                    "stage": "SECONDARY CASCADE",
                    "subsystem": "Mechanical Powertrain",
                    "parameter": "Crankshaft Rotational Speed (RPM)",
                    "nominal": 1500.0,
                    "projected": round(gen_rpm, 1),
                    "unit": "RPM",
                    "delta": f"-{rpm_drop} RPM (-{round((rpm_drop/1500)*100, 1)}%)",
                    "mechanism": "Electronic governor actuator automatically reduces fuel injection rack position to prevent piston-ring seizure.",
                },
                {
                    "stage": "SECONDARY CASCADE",
                    "subsystem": "Vibration Diagnostics",
                    "parameter": "Tri-Axial Bearing Vibration",
                    "nominal": 2.4,
                    "projected": round(gen_vib, 2),
                    "unit": "mm/s",
                    "delta": f"+{vib_rise} mm/s (+{round((vib_rise/2.4)*100, 1)}%)",
                    "mechanism": "Uneven thermodynamic combustion and torque harmonic distortion produce excessive radial displacement.",
                },
                {
                    "stage": "TERTIARY CASCADE",
                    "subsystem": "Microgrid Generation",
                    "parameter": "Generator Active Electrical Output",
                    "nominal": round(gen_kw + kw_loss, 1),
                    "projected": round(gen_kw, 1),
                    "unit": "kW",
                    "delta": f"-{kw_loss} kW (-{round((kw_loss/(gen_kw + kw_loss))*100, 1)}%)",
                    "mechanism": "Reduced angular velocity directly curtails stator alternating electromotive force.",
                },
                {
                    "stage": "QUATERNARY CASCADE",
                    "subsystem": "Battery Energy Storage (BESS)",
                    "parameter": "Battery Bank Discharge Current & SOC",
                    "nominal": "12.0 A / 88%",
                    "projected": f"{bess_discharge_a} A / {round(bess_soc)}%",
                    "unit": "A / %",
                    "delta": f"+{round(bess_discharge_a - 12.0)} A surge",
                    "mechanism": "Central switchboard inverter bus draws high instantaneous current from lithium storage to bridge power shortfall.",
                },
            ]

            sop_steps = [
                "Engage Auxiliary Generator Unit 3 via SCADA remote sync command.",
                "Shed non-essential thermal melting tanks and outdoor perimeter lighting.",
                "Deploy technician to clear snow buildup from generator intake louvers and check glycol level.",
                "Monitor vibration spectrum to avoid resonant frequencies in 1300-1400 RPM band.",
            ]

        # -------------------------------------------------------------
        # 2. SCENARIO: Catastrophic Generator Trip & Blackout Risk
        # -------------------------------------------------------------
        elif scenario_key in ["generator_trip_blackout"]:
            gen_temp = 104.0
            gen_rpm = 0.0
            gen_vib = 0.0
            gen_kw = 0.0
            bess_soc = 54.0
            bess_discharge_a = 145.0
            bess_temp = 31.0

            projected_state["station_health_score"] = 0.48
            projected_state["active_power_kw"] = 72.0

            if gen_primary_id in assets:
                assets[gen_primary_id]["health_score"] = 0.10
                assets[gen_primary_id]["operational_status"] = "FAILED"

            cascading_effects = [
                {
                    "stage": "PRIMARY TRIGGER",
                    "subsystem": "Primary Diesel Generator",
                    "parameter": "Generator Operational Breaker State",
                    "nominal": "CLOSED (68.0 kW)",
                    "projected": "TRIPPED (0.0 kW)",
                    "unit": "STATE",
                    "delta": "-68.0 kW INSTANT SHUTDOWN",
                    "mechanism": "Differential overcurrent relay tripped due to instantaneous ground fault.",
                },
                {
                    "stage": "SECONDARY CASCADE",
                    "subsystem": "Central Microgrid Switchgear",
                    "parameter": "High-Priority Load Shedding Level",
                    "nominal": "TIER 0 (ALL LOADS NORMAL)",
                    "projected": "TIER 2 (ESSENTIALS ONLY)",
                    "unit": "TIER",
                    "delta": "SHED 45 kW NON-CRITICAL",
                    "mechanism": "Automated PLC load shed disconnected science laboratories, sauna, and workshop outlets.",
                },
                {
                    "stage": "TERTIARY CASCADE",
                    "subsystem": "BESS Energy Storage",
                    "parameter": "Inverter DC Discharge Current",
                    "nominal": "12.0 A",
                    "projected": "145.0 A",
                    "unit": "AMPS",
                    "delta": "+133.0 A (12x SURGE)",
                    "mechanism": "Battery bank absorbing full baseline station life-support load.",
                },
            ]

            sop_steps = [
                "Execute immediate black-start sequence on Standby Emergency Generator 3.",
                "Verify BESS cell voltages remain above 2.85V emergency cutoff threshold.",
                "Notify station commander and confirm life-support HVAC circuits remain energized.",
            ]

        # -------------------------------------------------------------
        # 3. SCENARIO: Super-Blizzard & Life Support Thermal Stress
        # -------------------------------------------------------------
        elif scenario_key in ["polar_blizzard_thermal_stress", "extreme_weather"]:
            amb_delta = float(custom_params.get("temp_delta", -20.0))
            ambient_temp = -25.0 + amb_delta
            wind_speed = float(custom_params.get("wind_speed_kmh", 95.0))

            # Heating duty cycle increases drastically
            hvac_power_kw += round(abs(amb_delta) * 1.85, 1)
            fuel_burn_daily += round(abs(amb_delta) * 7.25, 1)
            hvac_flow = max(45.0, hvac_flow - 30.0) # Icing restrictions

            projected_state["station_health_score"] = 0.72
            projected_state["active_power_kw"] = round(projected_state.get("active_power_kw", 145.0) + (hvac_power_kw - 42.0), 1)

            cascading_effects = [
                {
                    "stage": "PRIMARY TRIGGER",
                    "subsystem": "Polar Meteorology",
                    "parameter": "Ambient Temperature & Wind Velocity",
                    "nominal": "-25.0°C / 28 km/h",
                    "projected": f"{ambient_temp}°C / {wind_speed} km/h",
                    "unit": "°C / km/h",
                    "delta": f"{amb_delta}°C / +{round(wind_speed - 28)} km/h",
                    "mechanism": "Catabatic polar vortex cold front passing directly over station sector.",
                },
                {
                    "stage": "SECONDARY CASCADE",
                    "subsystem": "Station Life Support HVAC",
                    "parameter": "Hydronic Loop Electrical Heating Demand",
                    "nominal": 42.0,
                    "projected": round(hvac_power_kw, 1),
                    "unit": "kW",
                    "delta": f"+{round(hvac_power_kw - 42.0, 1)} kW (+{round(((hvac_power_kw - 42)/42)*100)}%)",
                    "mechanism": "Dual 30 kW auxiliary resistance banks engage to sustain +18°C living habitat temperature.",
                },
                {
                    "stage": "TERTIARY CASCADE",
                    "subsystem": "Fuel Storage & Logistics",
                    "parameter": "Daily Polar Diesel Depletion Rate",
                    "nominal": round(fuel_burn_daily - abs(amb_delta) * 7.25),
                    "projected": round(fuel_burn_daily),
                    "unit": "LITERS / DAY",
                    "delta": f"+{round(abs(amb_delta) * 7.25)} L/d (+{round(((abs(amb_delta) * 7.25)/375)*100)}%)",
                    "mechanism": "Continuous high genset brake mean effective pressure (BMEP) elevates fuel consumption.",
                },
                {
                    "stage": "QUATERNARY CASCADE",
                    "subsystem": "Intake Ventilation",
                    "parameter": "Fresh Air Louver Intake Flow Rate",
                    "nominal": 85.0,
                    "projected": round(hvac_flow, 1),
                    "unit": "m³/min",
                    "delta": f"-{round(85.0 - hvac_flow, 1)} m³/min (-35%)",
                    "mechanism": "High-velocity drifting snow and rime frost accumulates on intake damper screens.",
                },
            ]

            sop_steps = [
                "Activate exterior intake screen de-icing heat trace circuits.",
                "Recirculate 80% indoor air through filtration scrubbers to reduce fresh air heating penalty.",
                "Verify fuel day-tank level every 2 hours.",
            ]

        # -------------------------------------------------------------
        # 4. SCENARIO: Polar Diesel Gelling & Fuel Starvation
        # -------------------------------------------------------------
        elif scenario_key in ["fuel_gelling_viscosity_loss", "fuel_critical"]:
            fuel_pressure_drop = 2.4
            gen_rpm_oscillation = 95.0
            gen_vib += 3.4
            gen_kw -= 22.0

            projected_state["station_health_score"] = 0.58

            cascading_effects = [
                {
                    "stage": "PRIMARY TRIGGER",
                    "subsystem": "Fuel Storage Battery",
                    "parameter": "Polar Diesel Bulk Temperature",
                    "nominal": "-22.0°C",
                    "projected": "-37.5°C",
                    "unit": "°C",
                    "delta": "-15.5°C BELOW CLOUD POINT",
                    "mechanism": "Extreme ground permafrost temperature drop causes micro-crystalline wax precipitation.",
                },
                {
                    "stage": "SECONDARY CASCADE",
                    "subsystem": "Fuel Transfer System",
                    "parameter": "Transfer Pump Delivery Line Pressure",
                    "nominal": 4.2,
                    "projected": 1.8,
                    "unit": "BAR",
                    "delta": f"-{fuel_pressure_drop} bar (-57%)",
                    "mechanism": "Viscous wax slurry chokes primary 10-micron fuel water separator cartridge.",
                },
                {
                    "stage": "TERTIARY CASCADE",
                    "subsystem": "Engine Speed Regulation",
                    "parameter": "Governor RPM Stability & Hunting",
                    "nominal": "1500 ± 2 RPM",
                    "projected": "1380 - 1530 RPM (HUNTING)",
                    "unit": "RPM",
                    "delta": f"±{gen_rpm_oscillation} RPM FLUCTUATION",
                    "mechanism": "Common rail pressure drops below injector minimum atomization threshold.",
                },
            ]

            sop_steps = [
                "Switch to internal heated day-tank supply loop immediately.",
                "Energize fuel line electric heat tracing cables along outdoor manifold.",
                "Replace primary fuel filter elements with pre-heated spares.",
            ]

        # -------------------------------------------------------------
        # 5. SCENARIO: Satellite Radome Servo Overload & Comms Loss
        # -------------------------------------------------------------
        elif scenario_key in ["satellite_radome_servo_overload", "comms_loss"]:
            comms_signal = 3.2
            projected_state["connectivity_status"] = "DEGRADED (LOCAL CACHE)"
            projected_state["station_health_score"] = 0.81

            cascading_effects = [
                {
                    "stage": "PRIMARY TRIGGER",
                    "subsystem": "Satellite Ground Station",
                    "parameter": "Azimuth Drive Servo Motor Current",
                    "nominal": "4.8 A",
                    "projected": "14.2 A (OVERTORQUE)",
                    "unit": "AMPS",
                    "delta": "+9.4 A (+195%)",
                    "mechanism": "115 km/h buffeting storm winds against 4.5m tracking radome dish.",
                },
                {
                    "stage": "SECONDARY CASCADE",
                    "subsystem": "RF Satellite Ground Link",
                    "parameter": "Ku-Band / AGEOS Carrier-to-Noise (C/N)",
                    "nominal": 18.5,
                    "projected": 1.8,
                    "unit": "dB",
                    "delta": "-16.7 dB LOSS",
                    "mechanism": "3.8° mechanical pointing offset causes total loss of main lobe beam alignment.",
                },
                {
                    "stage": "TERTIARY CASCADE",
                    "subsystem": "Mission Telemetry Ingestion",
                    "parameter": "SCADA Ground Stream Downlink Rate",
                    "nominal": "45.0 Mbps",
                    "projected": "0.05 Mbps (BUFFERED)",
                    "unit": "Mbps",
                    "delta": "BLACKOUT -> AUTONOMOUS LOGGING",
                    "mechanism": "Local SSD circular buffer activated to prevent telemetry frame loss.",
                },
            ]

            sop_steps = [
                "Lock antenna pedestal in survival stow position (elevation 90°).",
                "Activate HF ALE transceiver link with Maitri/Bharati sibling base for emergency voice.",
                "Verify local SCADA telemetry retention buffer is writing cleanly to NVMe arrays.",
            ]

        # -------------------------------------------------------------
        # 6. SCENARIO: Water Intake Freeze-Up
        # -------------------------------------------------------------
        elif scenario_key in ["water_intake_freeze_drought"]:
            water_flow = 0.0
            projected_state["station_health_score"] = 0.68

            cascading_effects = [
                {
                    "stage": "PRIMARY TRIGGER",
                    "subsystem": "Lake / Coastal Water Intake",
                    "parameter": "Intake Trace Heating Cable Resistance",
                    "nominal": "18.2 Ω",
                    "projected": "OPEN CIRCUIT (∞ Ω)",
                    "unit": "OHMS",
                    "delta": "HEATER COLD FAILURE",
                    "mechanism": "Permafrost ice shifting severed buried electric heat tape.",
                },
                {
                    "stage": "SECONDARY CASCADE",
                    "subsystem": "Meltwater Intake Pipeline",
                    "parameter": "Raw Water Intake Flow Rate",
                    "nominal": 160.0,
                    "projected": 0.0,
                    "unit": "LITERS / HOUR",
                    "delta": "-160.0 L/h (-100%)",
                    "mechanism": "Ice plug formed in intake conduit; pump tripped on dry-run safety sensor.",
                },
                {
                    "stage": "TERTIARY CASCADE",
                    "subsystem": "Station Life Support Reserves",
                    "parameter": "Potable Water Reserve Runway",
                    "nominal": "NOMINAL REPLENISHMENT",
                    "projected": "18 DAYS (RATIONED)",
                    "unit": "DAYS",
                    "delta": "RESERVE DEPLETION COMMENCED",
                    "mechanism": "Station forced onto static 8,200 L insulated storage tank.",
                },
            ]

            sop_steps = [
                "Engage emergency secondary thermal circulation pump on lake line.",
                "Enforce Station Water Conservation Protocol (Tier 1: 35L per person per day).",
                "Dispatch snowcat melt crew to auxiliary snow melter unit.",
            ]

        else:
            # Generic Custom Parameter Propagation
            custom_temp = float(custom_params.get("generator_temp", 85.0))
            gen_temp = custom_temp
            gen_rpm = max(1000.0, 1500.0 - (gen_temp - 78.0) * 8.0)
            gen_vib = 2.4 + max(0.0, (gen_temp - 78.0) * 0.25)
            projected_state["station_health_score"] = max(0.4, 0.95 - (gen_temp - 78.0) * 0.02)

            cascading_effects = [
                {
                    "stage": "CUSTOM PARAMETER INJECTION",
                    "subsystem": "Custom Injected Telemetry Delta",
                    "parameter": "Generator Operating Temperature",
                    "nominal": 78.0,
                    "projected": gen_temp,
                    "unit": "°C",
                    "delta": f"{gen_temp - 78.0:+.1f}°C",
                    "mechanism": "Custom injected operator parameter vector.",
                }
            ]
            sop_steps = ["Monitor station SCADA bus telemetry response to injected variable."]

        # =============================================================
        # DUAL-ML MODEL INFERENCE ON PROJECTED MULTI-VARIABLE STATE
        # =============================================================

        # 1. Isolation Forest Anomaly Detection
        feature_vector = {
            "temp": gen_temp,
            "rpm": gen_rpm,
            "vibration": gen_vib,
            "soc": bess_soc,
            "battery_temp": bess_temp,
            "flow": hvac_flow,
        }
        anomaly_score, is_anomaly = anomaly_detector.predict_anomaly(feature_vector)

        risk_level = "NOMINAL"
        if anomaly_score > 0.80:
            risk_level = "CRITICAL RISK"
        elif anomaly_score > 0.60:
            risk_level = "HIGH RISK"
        elif anomaly_score > 0.40:
            risk_level = "MODERATE ADVISORY"

        ml_anomaly_result = {
            "anomaly_score": round(anomaly_score, 3),
            "anomaly_probability_pct": round(anomaly_score * 100, 1),
            "is_anomaly": is_anomaly,
            "risk_level": risk_level,
            "evaluated_features": {
                "temperature_c": round(gen_temp, 1),
                "crankshaft_rpm": round(gen_rpm, 1),
                "bearing_vibration_mms": round(gen_vib, 2),
                "battery_soc_pct": round(bess_soc, 1),
                "battery_temp_c": round(bess_temp, 1),
                "hvac_intake_flow_m3min": round(hvac_flow, 1),
            },
            "model_architecture": "Isolation Forest ML Anomaly Engine (scikit-learn)",
            "model_confidence_pct": round(min(99.4, 75.0 + anomaly_score * 24.0), 1),
        }

        # 2. Random Forest 24-Hour Energy Load Forecast under Contingency
        ml_energy_forecast = energy_forecaster.forecast_24h(
            station_id=st_id, ambient_temp=ambient_temp
        )

        return {
            "station_id": st_id,
            "scenario": scenario_name,
            "scenario_metadata": next(
                (s for s in self.available_scenarios if s["id"] == scenario_name),
                {
                    "id": scenario_name,
                    "name": scenario_name.replace("_", " ").title(),
                    "category": "CONTINGENCY",
                    "description": "Multi-variable cascading contingency model.",
                },
            ),
            "current_state": {
                "station_health_score": current_state.get("station_health_score", 0.95),
                "active_power_kw": current_state.get("active_power_kw", 145.2 if is_maitri else 182.0),
                "generator_temp": 78.0,
                "generator_rpm": 1500.0,
                "generator_vibration": 2.4,
                "battery_soc": 88.0 if is_maitri else 94.0,
                "daily_fuel_l": 375.0 if is_maitri else 330.0,
                "ambient_temp_c": -25.0,
                "water_flow_lh": 160.0,
                "connectivity": "LIVE",
            },
            "projected_state": {
                "station_health_score": projected_state.get("station_health_score", 0.65),
                "active_power_kw": projected_state.get("active_power_kw", 110.0),
                "generator_temp": round(gen_temp, 1),
                "generator_rpm": round(gen_rpm, 1),
                "generator_vibration": round(gen_vib, 2),
                "battery_soc": round(bess_soc, 1),
                "daily_fuel_l": round(fuel_burn_daily, 1),
                "ambient_temp_c": round(ambient_temp, 1),
                "water_flow_lh": round(water_flow, 1),
                "connectivity": projected_state.get("connectivity_status", "LIVE"),
            },
            "cascading_effects": cascading_effects,
            "remediation_sop": sop_steps,
            "ml_anomaly_analysis": ml_anomaly_result,
            "ml_energy_forecast_24h": ml_energy_forecast[:12],  # Next 12 hours projection
            "simulated": True,
            "engine_version": "v2.0-physics-cascading-ml",
        }


scenario_engine = ScenarioEngine()
