import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd


class GoogleSheetsConnector:
    def __init__(self, key_file: str):
        self.scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(
            key_file, self.scope
        )
        self.client = gspread.authorize(self.creds)

    def read_sheet(self, sheet_id_or_name: str) -> pd.DataFrame:
        """Reads a Google Sheet by ID or Name into a DataFrame."""
        try:
            # Try opening by key (ID) first, then by title
            try:
                sheet = self.client.open_by_key(sheet_id_or_name).sheet1
            except gspread.exceptions.APIError:
                # If ID fails (e.g. it's a name), try open by title
                sheet = self.client.open(sheet_id_or_name).sheet1

            data = sheet.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error loading sheet {sheet_id_or_name}: {e}")
            return pd.DataFrame()

    def update_sheet(self, sheet_id_or_name: str, df: pd.DataFrame):
        """Overwrites a Google Sheet with the provided DataFrame."""
        try:
            try:
                sheet = self.client.open_by_key(sheet_id_or_name).sheet1
            except gspread.exceptions.APIError:
                sheet = self.client.open(sheet_id_or_name).sheet1

            # Clear existing data
            sheet.clear()

            # Update with new data (column headers + values)
            sheet.update([df.columns.values.tolist()] + df.values.tolist())
            return True
        except Exception as e:
            print(f"Error updating sheet {sheet_id_or_name}: {e}")
            return False
