import pandas as pd
from datetime import datetime
from src.utils import calculate_duration, normalize_string


class RosterManager:
    def __init__(self, data_handler):
        self.dh = data_handler

    def get_available_pilots(self, skill=None, location=None, date=None):
        """Filters pilots by status, skill, and location."""
        df = self.dh.get_pilots()
        # Basic filter: Status must be Available
        df = df[df["status"] == "Available"]

        if location:
            df = df[
                df["location"].apply(normalize_string) == normalize_string(location)
            ]

        if skill:
            df = df[
                df["skills"].apply(
                    lambda x: normalize_string(skill) in normalize_string(x)
                )
            ]

        # TODO: Date availability check (available_from <= date)
        if date:
            date_dt = pd.to_datetime(date)
            df = df[pd.to_datetime(df["available_from"]) <= date_dt]

        return df

    def calculate_cost(self, pilot_id, duration_days):
        """Calculates total cost for a pilot."""
        pilot = self.dh.get_pilots()[self.dh.get_pilots()["pilot_id"] == pilot_id]
        if not pilot.empty:
            rate = pilot.iloc[0]["daily_rate_inr"]
            return rate * duration_days
        return 0


class FleetManager:
    def __init__(self, data_handler):
        self.dh = data_handler

    def get_available_drones(self, capability=None, location=None):
        df = self.dh.get_drones()
        df = df[df["status"] == "Available"]

        if location:
            df = df[
                df["location"].apply(normalize_string) == normalize_string(location)
            ]

        if capability:
            df = df[
                df["capabilities"].apply(
                    lambda x: normalize_string(capability) in normalize_string(x)
                )
            ]

        return df

    def check_weather_compatibility(self, drone_id, weather_condition):
        """Checks if a drone can fly in the given weather."""
        drone = self.dh.get_drones()[self.dh.get_drones()["drone_id"] == drone_id]
        if drone.empty:
            return False

        resistance = drone.iloc[0]["weather_resistance"]
        # Simple logic: If 'None' and weather is Rain/Storm, return False.
        # If IP43, it can handle Rain.

        weather = normalize_string(weather_condition)
        res_norm = normalize_string(resistance)

        if "rain" in weather:
            if "none" in res_norm:
                return False

        return True


class ConflictDetector:
    def __init__(self, data_handler):
        self.dh = data_handler
        self.roster_mgr = RosterManager(data_handler)

    def check_assignment(self, pilot_id, drone_id, mission_id):
        issues = []
        mission = self.dh.get_missions()[
            self.dh.get_missions()["project_id"] == mission_id
        ].iloc[0]
        pilot = self.dh.get_pilots()[self.dh.get_pilots()["pilot_id"] == pilot_id].iloc[
            0
        ]
        drone = self.dh.get_drones()[self.dh.get_drones()["drone_id"] == drone_id].iloc[
            0
        ]

        # 1. Budget Check
        duration = calculate_duration(mission["start_date"], mission["end_date"])
        cost = self.roster_mgr.calculate_cost(pilot_id, duration)
        if cost > mission["mission_budget_inr"]:
            issues.append(
                f"Budget Overrun: Pilot cost {cost} > Budget {mission['mission_budget_inr']}"
            )

        # 2. Certification Check
        req_certs = [c.strip() for c in mission["required_certs"].split(",")]
        pilot_certs = pilot["certifications"]
        for cert in req_certs:
            if normalize_string(cert) not in normalize_string(pilot_certs):
                issues.append(f"Missing Certification: Pilot lacks {cert}")

        # 3. Weather/Drone Check
        # TODO: Implement Helper in FleetManager to be called here or standalone

        return issues

    def check_all_active_conflicts(self):
        """Checks conflicts for all active assignments."""
        issues = []
        pilots = self.dh.get_pilots()
        drones = self.dh.get_drones()

        # Filter accepted assignments
        assigned_pilots = pilots[pilots["current_assignment"] != "-"]

        for _, pilot in assigned_pilots.iterrows():
            mission_id = pilot["current_assignment"]
            pilot_id = pilot["pilot_id"]

            # Find drone assigned to same mission
            assigned_drone = drones[drones["current_assignment"] == mission_id]

            if assigned_drone.empty:
                issues.append(
                    f"⚠️ Mission {mission_id}: Pilot {pilot['name']} assigned but no Drone assigned."
                )
                continue

            drone_id = assigned_drone.iloc[0]["drone_id"]

            try:
                # Check for conflicts
                conflict_list = self.check_assignment(pilot_id, drone_id, mission_id)
                if conflict_list:
                    for c in conflict_list:
                        issues.append(f"🚨 Mission {mission_id} Conflict: {c}")
            except Exception as e:
                # Fallback if mission ID doesn't match or other data issue
                issues.append(f"⚠️ Error checking Mission {mission_id}: {e}")

        return issues
