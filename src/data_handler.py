import pandas as pd
import os
from typing import Optional, Dict, Any, List
from src.sheets_sync import GoogleSheetsConnector

try:
    from dotenv import load_dotenv

    load_dotenv()
except:
    pass


class DataHandler:
    def __init__(
        self,
        pilot_file: str,
        drone_file: str,
        mission_file: str,
        gsheets_creds: Optional[str] = None,
        sheet_mapping: Optional[Dict[str, str]] = None,
    ):
        self.files = {
            "pilots": pilot_file,
            "drones": drone_file,
            "missions": mission_file,
        }
        self.data = {}
        self.gsheets_creds = gsheets_creds
        self.connector = None
        self.sheet_mapping = sheet_mapping or {}

        # Check for Sheet IDs in env
        self.sheet_ids = {
            "pilots": os.getenv("PILOT_SHEET_ID"),
            "drones": os.getenv("DRONE_SHEET_ID"),
            "missions": os.getenv("MISSIONS_SHEET_ID"),
        }

        # Load initial data
        self.load_data()

        # Initialize Sheets Connector if creds exist
        if self.gsheets_creds and os.path.exists(self.gsheets_creds):
            try:
                self.connector = GoogleSheetsConnector(self.gsheets_creds)
                print("✅ Google Sheets Connector Initialized")
            except Exception as e:
                print(f"⚠️ Failed to initialize Google Sheets: {e}")
        else:
            print("⚠️ No credentials found. Attempting to fetch public sheets...")
            self.sync_from_public_sheets()

    def sync_from_public_sheets(self):
        """Attempts to load data from public Google Sheet URLs."""
        for key, sheet_id in self.sheet_ids.items():
            if not sheet_id or "your_" in sheet_id:
                continue

            try:
                url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
                df = pd.read_csv(url)
                if not df.empty:
                    self.data[key] = df
                    self.save_data(key)  # Update local CSV
                    print(f"✅ Pulled {key} from public sheet")
            except Exception as e:
                print(f"⚠️ Could not pull {key} from public sheet: {e}")

    def load_data(self):
        """Loads data from CSV files."""
        for key, filepath in self.files.items():
            if os.path.exists(filepath):
                self.data[key] = pd.read_csv(filepath)
            else:
                # Create empty dataframe with expected columns if file missing
                self.data[key] = pd.DataFrame()
                print(f"⚠️ Warning: {filepath} not found. Created empty DataFrame.")

    def save_data(self, key: str):
        """Saves current dataframe to CSV."""
        if key in self.files and key in self.data:
            self.data[key].to_csv(self.files[key], index=False)

    def sync_to_sheets(self):
        """Syncs local data to Google Sheets."""
        if not self.connector:
            return "Google Sheets not configured."

        results = []
        for key, df in self.data.items():
            sheet_name = self.sheet_mapping.get(key)
            sheet_id = self.sheet_ids.get(key)

            # Use Sheet ID if available, otherwise name
            target = sheet_id if sheet_id else sheet_name

            if target:
                try:
                    self.connector.update_sheet(target, df)
                    results.append(f"✅ Synced {key}")
                except Exception as e:
                    results.append(f"❌ Failed {key}: {e}")
        return "\n".join(results)

    def sync_from_sheets(self):
        """Pull data from Google Sheets."""
        if not self.connector:
            return "Google Sheets not configured."

        results = []
        for key in self.data.keys():
            sheet_name = self.sheet_mapping.get(key)
            sheet_id = self.sheet_ids.get(key)
            target = sheet_id if sheet_id else sheet_name

            if target:
                try:
                    new_df = self.connector.read_sheet(target)
                    if not new_df.empty:
                        self.data[key] = new_df
                        self.save_data(key)  # Update local CSV
                        results.append(f"✅ Pulled {key}")
                except Exception as e:
                    results.append(f"❌ Failed {key}: {e}")
        return "\n".join(results)

    # Getters
    def get_pilots(self):
        return self.data.get("pilots", pd.DataFrame())

    def get_drones(self):
        return self.data.get("drones", pd.DataFrame())

    def get_missions(self):
        return self.data.get("missions", pd.DataFrame())

    # Setters
    def update_pilots(self, df):
        self.data["pilots"] = df
        self.save_data("pilots")

    def update_drones(self, df):
        self.data["drones"] = df
        self.save_data("drones")
