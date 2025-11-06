"""
A centralized registry for all scheduled task IDs.

This prevents circular dependencies by allowing any part of the application
(e.g., schedulers, API endpoints) to reference a task by its ID without
needing to import the task function itself.
"""
# --- Scheduled Task IDs ---
CATALOG_TASK_ID = "scheduled_catalog_update"
SET_CATALOG_TASK_ID = "scheduled_set_catalog_update"
FULL_CATALOG_TASK_ID = "scheduled_full_catalog_update"
AVAILABILITY_TASK_ID = "scheduled_availability_update"

# --- One-Off Task IDs ---
UPDATE_WANTED_CARDS_AVAILABILITY = "update_wanted_cards_availability"
UPDATE_AVAILABILITY_SINGLE_CARD = "update_availability_single_card"