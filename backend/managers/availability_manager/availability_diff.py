from typing import Dict, List, TypedDict

from utility import logger


# Type Aliases for clarity
Listing = Dict[str, str]
StoreAvailability = Dict[str, List[Listing]]
CardAvailability = Dict[str, StoreAvailability]


class UpdateDetail(TypedDict):
    """Represents the new and removed listings for a card at a specific store."""

    new: List[Listing]
    removed: List[Listing]


UpdatedStoreInfo = Dict[str, UpdateDetail]
UpdatedCards = Dict[str, UpdatedStoreInfo]


class Changes(TypedDict):
    """Represents the overall changes in card availability."""

    added: CardAvailability
    removed: CardAvailability
    updated: UpdatedCards


def detect_changes(
    old_availability: CardAvailability, new_availability: CardAvailability
) -> Changes:
    """Detects differences between two availability states."""
    logger.info("🔄 Detecting changes in availability data...")

    changes: Changes = {"added": {}, "removed": {}, "updated": {}}

    # Detect removed cards
    for card in old_availability.keys():
        if card not in new_availability:
            changes["removed"][card] = old_availability[card]

    # Detect new or updated cards
    for card, stores in new_availability.items():
        if card not in old_availability:
            changes["added"][card] = stores
        else:
            for store, new_listings in stores.items():
                old_listings = old_availability[card].get(store, [])
                if old_listings != new_listings:
                    changes["updated"].setdefault(card, {})[store] = {
                        "new": [
                            l for l in new_listings if l not in old_listings
                        ],
                        "removed": [
                            l for l in old_listings if l not in new_listings
                        ],
                    }

    logger.info(
        f"✅ Changes detected: {sum(len(v) for v in changes.values())} total."
    )
    return changes
