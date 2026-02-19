# Skylark Drone Operations Agent 🚁

An AI-powered dashboard for managing drone pilots, fleets, and missions. This system integrates with Google Sheets for real-time data and uses Google's Gemini API for intelligent reasoning.

## 🌟 Key Features

### 1. **Robust Dual-Mode Intelligence**
This system is designed for maximum reliability:
-   **Primary Mode (API Enabled)**: The system first attempts to use the **Google Gemini API** (using multiple rotated keys). It has full reasoning capabilities to answer complex queries about availability, conflicts, and resource allocation.
-   **Backup Mode (Offline/Local)**: If all API keys fail (due to quota limits or connectivity issues), the system **automatically and silently falls back** to a "Trained Logic" mode. In this mode, it uses local Python logic and the manual context file (`src/system_prompts.py`) to answer critical questions like checking availability or detecting conflicts.

### 2. **Manual Training & Context**
You can "manually train" the agent by editing `src/system_prompts.py`.
-   Add new business rules (e.g., "Pilots need 8 hours rest").
-   Define new data columns you add to your sheets.
-   **Dynamic Adaptation**: The agent reads this file and your current sheet schema for *every* query, so changes apply instantly.

### 3. **Sheet Agnostic**
The system automatically detects column names from your Google Sheets. If you change your sheet structure (e.g., rename "Location" to "Base"), you don't need to rewrite the code—just update the context in `src/system_prompts.py` so the agent knows what the new column means.

## 🚀 Setup & Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/Shamanth-8/skylarkdrone.git
    cd skylarkdrone
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration**
    Create a `.env` file in the root directory (do not commit this file!):
    ```env
    GOOGLE_API_KEY=your_api_key_1,your_api_key_2
    PILOT_SHEET_ID=your_pilot_sheet_id
    DRONE_SHEET_ID=your_drone_sheet_id
    MISSIONS_SHEET_ID=your_missions_sheet_id
    ```
    *Note: Google Sheets must be set to "Anyone with the link can view" to work without a service account file.*

4.  **Run the Application**
    ```bash
    streamlit run app.py
    ```

## 📂 Project Structure

-   `app.py`: Main Streamlit dashboard application.
-   `src/agent.py`: The AI agent logic (Primary API + Offline Fallback).
-   `src/system_prompts.py`: **Manual Training File**. Edit this to add rules.
-   `src/logic.py`: Core business logic (conflict detection, cost calculation).
-   `src/data_handler.py`: Manages data syncing with Google Sheets.
-   `DECISION_LOG.md`: [Read the Design Decisions & Trade-offs](./DECISION_LOG.md).

## ⚠️ Important Notes

-   **API Quota**: The system supports multiple API keys in `.env` (comma-separated). It rotates them automatically to avoid hitting rate limits.
-   **Data Security**: Your `.env` file containing keys is ignored by Git. Only the `requirements.txt` and code are pushed.
