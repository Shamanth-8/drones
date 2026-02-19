import google.generativeai as genai
from src.logic import RosterManager, FleetManager, ConflictDetector
from src.system_prompts import MANUAL_CONTEXT
import time
import random


class DroneAgent:
    def __init__(self, data_handler, api_key=None):
        self.dh = data_handler
        self.roster_mgr = RosterManager(data_handler)
        self.fleet_mgr = FleetManager(data_handler)
        self.conflict_det = ConflictDetector(data_handler)

        # Parse API Keys (comma separated)
        self.api_keys = []
        if api_key:
            self.api_keys = [k.strip() for k in api_key.split(",") if k.strip()]

        # Start with a random key to distribute load if multiple keys exist
        self.current_key_index = (
            random.randint(0, len(self.api_keys) - 1) if self.api_keys else 0
        )
        self.model_name = "gemini-2.0-flash"

    def _configure_genai(self):
        """Configures GenAI with the current key."""
        if not self.api_keys:
            return False

        current_key = self.api_keys[self.current_key_index]
        genai.configure(api_key=current_key)
        return True

    def _rotate_key(self):
        """Switches to the next available API Key."""
        if len(self.api_keys) <= 1:
            return False  # No other keys to rotate to

        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        # print(f"🔄 Check 429: Rotating to API Key #{self.current_key_index + 1}")
        return True

    def process_query(self, query):
        if not self.api_keys:
            return self.mock_response(query)

        # Define Tools with Optimization (Limit output size)
        def check_availability(location: str = None, skill: str = None):
            """Check which pilots are available based on criteria."""
            df = self.roster_mgr.get_available_pilots(location=location, skill=skill)
            # LIMIT: Only show top 10 results to save tokens and avoid Rate Limit
            return df.head(10).to_string(index=False)

        def check_drone_inventory(location: str = None, capability: str = None):
            """Check drone inventory based on location and capability."""
            df = self.fleet_mgr.get_available_drones(
                location=location, capability=capability
            )
            # LIMIT: Only show top 10 results to save tokens and avoid Rate Limit
            return df.head(10).to_string(index=False)

        def update_pilot_status(pilot_id: str, status: str):
            """Updates a pilot's status (Available, On Leave, Assigned) and syncs."""
            df = self.dh.get_pilots()
            if pilot_id not in df["pilot_id"].values:
                return f"Error: Pilot {pilot_id} not found."

            # Update local
            df.loc[df["pilot_id"] == pilot_id, "status"] = status
            self.dh.update_pilots(df)

            # Try sync
            sync_res = self.dh.sync_to_sheets()
            return f"Updated {pilot_id} to {status}. Sync Result: {sync_res}"

        def update_drone_status(drone_id: str, status: str):
            """Updates a drone's status (Available, Maintenance, Deployed) and syncs."""
            df = self.dh.get_drones()
            if drone_id not in df["drone_id"].values:
                return f"Error: Drone {drone_id} not found."

            # Update local
            df.loc[df["drone_id"] == drone_id, "status"] = status
            self.dh.update_drones(df)

            # Try sync
            sync_res = self.dh.sync_to_sheets()
            return f"Updated {drone_id} to {status}. Sync Result: {sync_res}"

        tools = [
            check_availability,
            check_drone_inventory,
            update_pilot_status,
            update_drone_status,
        ]

        # Retry logic with Key Rotation
        # Try enough times to exhaust all keys if needed
        max_retries = len(self.api_keys) * 2 if self.api_keys else 1

        last_error = None

        for attempt in range(max_retries):
            try:
                # Configure with current key
                if not self._configure_genai():
                    return self.mock_response(query)

                model = genai.GenerativeModel(model_name=self.model_name, tools=tools)

                chat = model.start_chat(enable_automatic_function_calling=True)

                # Construct Dynamic System Prompt
                # 1. Schema Info
                schema_info = "## Current Data Schema\n"
                for name, df in self.dh.data.items():
                    if not df.empty:
                        schema_info += f"- **{name.capitalize()} Columns**: {', '.join(df.columns.tolist())}\n"

                # 2. Combine all context
                system_instruction = (
                    "You are a Drone Operations Coordinator. Use the provided tools to answer queries.\n\n"
                    f"{schema_info}\n"
                    f"{MANUAL_CONTEXT}\n"
                    "Always check the schema columns to see if new data fields are available to answer the user's question."
                )

                response = chat.send_message(
                    f"System: {system_instruction}\nUser: {query}"
                )
                return response.text

            except Exception as e:
                last_error = str(e)
                # print(f"⚠️ API Error (Attempt {attempt+1}/{max_retries}): {e}")

                # Check for Rate Limit (429) or Quota Exceeded (403/429)
                if "429" in last_error or "403" in last_error or "Quota" in last_error:
                    # Try rotating keys
                    if self._rotate_key():
                        continue

                    # If we can't rotate (only 1 key) or have rotated through all, wait a bit
                    time.sleep(1)
                    continue

                # For other errors, we might not want to retry, but let's be safe and try rotating once just in case
                if self._rotate_key():
                    continue
                break

        # Final Fallback to Offline Mode (Silent Failover)
        return self.mock_response(query)

    def mock_response(self, query):
        """Simple keyword matching for prototype without API key."""
        query = query.lower()

        # 1. Availability Check
        if "available" in query and "pilot" in query:
            pilots = self.roster_mgr.get_available_pilots()
            if pilots.empty:
                return "No pilots available."
            return f"**Here are the Available Pilots:**\n\n```\n{pilots[['name', 'location', 'skills']].to_string(index=False)}\n```"

        # 2. Drone check
        if "drone" in query:
            drones = self.fleet_mgr.get_available_drones()
            if drones.empty:
                return "No drones available."
            return f"**Here are the Available Drones:**\n\n```\n{drones[['model', 'location', 'capabilities']].to_string(index=False)}\n```"

        # 3. Conflict Check
        if "conflict" in query:
            issues = self.conflict_det.check_all_active_conflicts()
            if not issues:
                return "✅ **No active conflicts detected in current assignments.**"

            report = "**⚠️ Active Conflicts Detected:**\n\n"
            for issue in issues:
                report += f"- {issue}\n"
            return report

        # Fallback for unknown queries
        return "I can help you check **availability**, **drones**, or **conflicts**. What would you like to know?"
