import copy
from typing import Dict, Any
from app.digital_twin.engine import digital_twin_engine


class ScenarioEngine:
    def run_scenario(self, station_id: str, scenario_name: str) -> Dict[str, Any]:
        st_id = station_id.lower()
        current_state = digital_twin_engine.get_station_state(st_id)
        if not current_state:
            return {}

        projected_state = copy.deepcopy(current_state)
        assets = projected_state.get("assets", {})

        if scenario_name == "generator_failure":
            gen1_key = "GEN-MAI-001" if st_id == "maitri" else "GEN-BHA-001"
            if gen1_key in assets:
                assets[gen1_key]["operational_status"] = "FAILED"
                assets[gen1_key]["health_score"] = 0.15
                assets[gen1_key]["sensor_readings"]["status"] = 0.0
                assets[gen1_key]["sensor_readings"]["temperature"] = 98.0
            projected_state["station_health_score"] = 0.65

        elif scenario_name == "extreme_weather":
            for aid, a in assets.items():
                if a["asset_type"] == "HVAC":
                    a["sensor_readings"]["flow_rate"] = 95.0
            projected_state["station_health_score"] = 0.82

        elif scenario_name == "comms_loss":
            com_key = "COM-MAI-001" if st_id == "maitri" else "COM-BHA-001"
            if com_key in assets:
                assets[com_key]["operational_status"] = "FAILED"
                assets[com_key]["connectivity"] = "OFFLINE"
                assets[com_key]["sensor_readings"]["signal_strength"] = 0.0
            projected_state["connectivity_status"] = "DEGRADED"

        elif scenario_name == "fuel_critical":
            projected_state["station_health_score"] = 0.55

        return {
            "station_id": st_id,
            "scenario": scenario_name,
            "current_state": current_state,
            "projected_state": projected_state,
            "simulated": True,
        }


scenario_engine = ScenarioEngine()
