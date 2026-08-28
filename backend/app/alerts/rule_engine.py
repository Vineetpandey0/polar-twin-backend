from typing import List, Dict, Any
from app.schemas.alert import AlertCreate


class RuleEngine:
    def evaluate_station(self, station_state: Dict[str, Any]) -> List[AlertCreate]:
        alerts: List[AlertCreate] = []
        station_id = station_state.get("station_id", "")
        assets = station_state.get("assets", {})

        # Track status for compound rules
        gen_failed = False
        bat_critical = False

        for aid, asset in assets.items():
            atype = asset.get("asset_type")
            readings = asset.get("sensor_readings", {})
            status = asset.get("operational_status")

            if status == "FAILED":
                if atype == "GENERATOR":
                    gen_failed = True
                alerts.append(
                    AlertCreate(
                        station_id=station_id,
                        asset_id=aid,
                        severity="CRITICAL",
                        message=f"{asset.get('name')} HAS FAILED",
                        reason=f"Asset operational status reported FAILED.",
                    )
                )

            # Generator rules
            if atype == "GENERATOR":
                temp = readings.get("temperature", 0.0)
                if temp > 95.0:
                    alerts.append(AlertCreate(station_id=station_id, asset_id=aid, severity="CRITICAL", message=f"{aid} Overheating", reason=f"Temperature {temp}°C exceeded critical threshold (95°C)"))
                elif temp > 85.0:
                    alerts.append(AlertCreate(station_id=station_id, asset_id=aid, severity="WARNING", message=f"{aid} High Temperature", reason=f"Temperature {temp}°C exceeded warning threshold (85°C)"))

            # Battery rules
            elif atype == "BATTERY":
                soc = readings.get("soc", 100.0)
                if soc < 10.0:
                    bat_critical = True
                    alerts.append(AlertCreate(station_id=station_id, asset_id=aid, severity="CRITICAL", message=f"{aid} Battery Depleted", reason=f"State of charge {soc}% is below 10%"))
                elif soc < 20.0:
                    alerts.append(AlertCreate(station_id=station_id, asset_id=aid, severity="WARNING", message=f"{aid} Battery Low", reason=f"State of charge {soc}% is below 20%"))

            # Comms rules
            elif atype == "COMMS":
                sig = readings.get("signal_strength", 100.0)
                if sig < 1.0 or status == "FAILED":
                    alerts.append(AlertCreate(station_id=station_id, asset_id=aid, severity="CRITICAL", message=f"{aid} Comms Lost", reason="Signal strength 0% / Satellite link down"))
                elif sig < 20.0:
                    alerts.append(AlertCreate(station_id=station_id, asset_id=aid, severity="WARNING", message=f"{aid} Weak Comms Signal", reason=f"Signal strength {sig}% below 20%"))

        # Compound rule: Battery CRITICAL + Generator FAILED
        if gen_failed and bat_critical:
            alerts.append(
                AlertCreate(
                    station_id=station_id,
                    asset_id=None,
                    severity="CRITICAL",
                    message="STATION POWER BLACKOUT RISK",
                    reason="Primary Generator Failed AND Battery Depleted below 10%",
                )
            )

        return alerts


rule_engine = RuleEngine()
