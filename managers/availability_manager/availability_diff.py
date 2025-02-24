from utility.logger import logger


def detect_changes(old_availability, new_availability):
    """Detects differences between two availability states."""
    logger.info("🔄 Detecting changes in availability data...")

    changes = {"added": {}, "removed": {}, "updated": {}}

    if not old_availability:
        logger.info(f"🚨 No previous availability found")
    else:
        # Detect removed cards
        for card in old_availability.keys():
            if card not in new_availability:
                changes["removed"][card] = old_availability[card]

    if not new_availability:
        logger.info(f"🚨 No new availability found")
        return []
    # Detect new or updated cards
    for card, stores in new_availability.items():
        if card not in old_availability:
            changes["added"][card] = stores
        else:
            for store, new_listings in stores.items():
                old_listings = old_availability[card].get(store, [])
                if old_listings != new_listings:
                    changes["updated"].setdefault(card, {})[store] = {
                        "new": [l for l in new_listings if l not in old_listings],
                        "removed": [l for l in old_listings if l not in new_listings],
                    }

    logger.info(f"✅ Changes detected: {sum(len(v) for v in changes.values())} total.")
    return changes
