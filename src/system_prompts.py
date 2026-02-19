# manual_training_data
# You can edit this string to "train" the agent on new rules, data definitions, or business logic.
# The agent will read this every time it processes a query.

MANUAL_CONTEXT = """
# Domain Knowledge & Rules

- **Pilots**:
    - "Available" status means they are ready for deployment.
    - "DGCA" certification is mandatory for all commercial flights.
    - Rate is in INR per day.

- **Drones**:
    - "Maintenance" status means the drone cannot be flown.
    - IP43 rating allows flying in light rain.
    - "Thermal" capability is required for night surveillance.

- **Missions**:
    - Priority levels: Normal, High, Urgent.
    - Budget is strictly enforced.

# New Data Instructions
If you add new columns to the sheets, describe them here so I understand what they mean.
For example:
- "battery_cycles": The number of charge cycles the drone battery has undergone. >300 requires checkup.
"""
