from typing import Dict, Any
from app.digital_twin.engine import digital_twin_engine
from app.simulation.scenario_engine import scenario_engine
from app.analytics.energy_forecaster import energy_forecaster

AI_TOOLS_SCHEMA = [
    {
        "name": "get_station_state",
        "description": "Get current real-time state, health score, and energy balance for a station.",
        "input_schema": {
            "type": "object",
            "properties": {"station_id": {"type": "string", "description": "maitri or bharati"}},
            "required": ["station_id"],
        },
    },
    {
        "name": "get_asset_detail",
        "description": "Get detailed telemetry and status of a specific asset.",
        "input_schema": {
            "type": "object",
            "properties": {
                "station_id": {"type": "string"},
                "asset_id": {"type": "string"},
            },
            "required": ["station_id", "asset_id"],
        },
    },
    {
        "name": "get_active_alerts",
        "description": "Get all active warning and critical alerts for a station.",
        "input_schema": {
            "type": "object",
            "properties": {"station_id": {"type": "string"}},
            "required": ["station_id"],
        },
    },
    {
        "name": "get_energy_forecast",
        "description": "Get 24-hour predictive energy generation and load forecast curve.",
        "input_schema": {
            "type": "object",
            "properties": {"station_id": {"type": "string"}},
            "required": ["station_id"],
        },
    },
    {
        "name": "get_inventory_status",
        "description": "Get current fuel, food, medical, and spare parts inventory.",
        "input_schema": {
            "type": "object",
            "properties": {"station_id": {"type": "string"}},
            "required": ["station_id"],
        },
    },
    {
        "name": "run_scenario",
        "description": "Simulate what-if scenarios (generator_failure, extreme_weather, comms_loss, fuel_critical).",
        "input_schema": {
            "type": "object",
            "properties": {
                "station_id": {"type": "string"},
                "scenario": {"type": "string"},
            },
            "required": ["station_id", "scenario"],
        },
    },
]


def execute_tool(tool_name: str, tool_args: dict) -> dict:
    station_id = tool_args.get("station_id", "maitri").lower()

    if tool_name == "get_station_state":
        res = digital_twin_engine.get_station_state(station_id)
        return res or {"error": "Station not found"}

    elif tool_name == "get_asset_detail":
        asset_id = tool_args.get("asset_id", "")
        res = digital_twin_engine.get_asset_state(station_id, asset_id)
        return res or {"error": "Asset not found"}

    elif tool_name == "get_active_alerts":
        state = digital_twin_engine.get_station_state(station_id)
        alerts = []
        if state:
            for aid, a in state.get("assets", {}).items():
                if a.get("operational_status") == "FAILED":
                    alerts.append({"asset_id": aid, "severity": "CRITICAL", "message": f"{a['name']} failure detected."})
                elif a.get("health_score", 1.0) < 0.8:
                    alerts.append({"asset_id": aid, "severity": "WARNING", "message": f"{a['name']} health degraded."})
        return {"station_id": station_id, "active_alerts": alerts}

    elif tool_name == "get_energy_forecast":
        forecasts = energy_forecaster.forecast_24h(station_id)
        return {"station_id": station_id, "forecasts": forecasts[:6]}

    elif tool_name == "get_inventory_status":
        return {
            "station_id": station_id,
            "fuel_liters": 45000 if station_id == "maitri" else 60000,
            "food_days": 120 if station_id == "maitri" else 180,
            "medical_status": "100%",
            "simulated": True,
        }

    elif tool_name == "run_scenario":
        scen = tool_args.get("scenario", "generator_failure")
        return scenario_engine.run_scenario(station_id, scen)

    return {"error": f"Unknown tool {tool_name}"}
