# Decision Log

## 1. Assumptions

*   **Data Integrity**: I assumed the CSV structure provided in the requirements is the source of truth. However, to make the system robust, I implemented a dynamic schema reader (`src/system_prompts.py`) that allows the agent to adapt if columns change.
*   **Public vs. Private Sheets**: Since the user initially lacked credentials, I assumed a "Local First" approach. The system defaults to local CSVs and attempts to read public Google Sheets if credentials are missing. Write-back functionality requires valid `credentials.json`.
*   **Conflict Definition**: I assumed a conflict exists if a pilot is assigned but has no drone, or if the drone/pilot capabilities do not match the mission requirements (e.g., Weather resistance).

## 2. Trade-offs

*   **API vs. Local Logic**:
    *   *Decision*: Use Gemini API for complex reasoning (matching skills, understanding "urgent") but fall back to hard-coded Python logic for strict rule validation (conflicts).
    *   *Why*: LLMs can hallucinate on strict math/logic constraints. Hard-coded logic (`src/logic.py`) ensures 100% accuracy for safety-critical checks like budget and certification.
*   **Synchronous Syncing**:
    *   *Decision*: Sync to Google Sheets immediately after an update.
    *   *Why*: Ensures data consistency across the team. The trade-off is latency; the user has to wait for the HTTP request to complete.
*   **Stateless Agent**:
    *   *Decision*: The agent does not maintain conversation history beyond the active session.
    *   *Why*: Simplifies the architecture and prevents "context drift". The state is stored in the Data (CSVs/Sheets), which is the single source of truth.

## 3. "Urgent Reassignments" Interpretation

The requirement stated: *"The agent should help coordinate urgent reassignments"*.

**My Interpretation**:
Urgent reassignments require finding the *best possible substitute* immediately, even if it ignores some soft constraints (like cost), but *never* safety constraints (like certifications).

**Implementation**:
I prompted the agent (via `src/system_prompts.py` and system instructions) to prioritize "Available" pilots who match the *location* of the urgent mission first. If an "Urgent" keyword is detected, the agent is instructed to:
1.  Look for pilots currently "On Leave" who might be recalled (if availability dates allow).
2.  Suggest swapping a pilot from a lower-priority mission.
3.  Flag the change clearly for human approval.

## 4. Tech Stack Justification

*   **Python + Streamlit**: Chosen for rapid prototyping and ease of use. It allows creating a functional UI in minutes.
*   **Google Gemini 2.0 Flash**: Selected for its low latency and high reasoning capability, which is crucial for a real-time operations agent.
*   **Pandas**: The industry standard for tabular data manipulation, essential for handling roster and fleet data efficiently.
