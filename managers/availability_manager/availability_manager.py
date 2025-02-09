import os
from managers.availability_manager.availability_storage import load_availability, save_availability
from managers.availability_manager.availability_diff import detect_changes
from managers.availability_manager.availability_update import fetch_latest_availability
from utility.logger import logger

def check_availability(username):
    """Retrieves and compares availability data, returning updates."""
    logger.info(f"🔍 Checking availability for {username}")

    # Load current availability
    current_availability = load_availability(username)

    # Get latest availability from sources
    updated_availability = fetch_latest_availability()

    # Compare old vs new
    changes = detect_changes(current_availability, updated_availability)

    # Save updated availability
    save_availability(username, updated_availability)

    return changes
