import os
from core.store_manager import load_store_availability
from user_manager import get_user, get_user_directory, load_card_list, load_json, save_json

current_availability = {}

def availability_diff(availability_update):
    """
    Detect changes between the current availability and the updated availability.
    Updates the current availability and returns a dictionary with changes.
    """
    global current_availability
    changes = {
        "added": {},  # Cards newly available
        "removed": {},  # Cards no longer available
        "updated": {}  # Cards with updated listings
    }

    # Detect removed cards
    for card_name in current_availability.keys():
        if card_name not in availability_update:
            changes["removed"][card_name] = current_availability[card_name]

    # Detect new or updated cards
    for card_name, stores in availability_update.items():
        if card_name not in current_availability:
            changes["added"][card_name] = stores
        else:
            for store, new_listings in stores.items():
                if store not in current_availability[card_name]:
                    if card_name not in changes["added"]:
                        changes["added"][card_name] = {}
                    changes["added"][card_name][store] = new_listings
                else:
                    old_listings = current_availability[card_name][store]
                    # Compare listings
                    if old_listings != new_listings:
                        if card_name not in changes["updated"]:
                            changes["updated"][card_name] = {}
                        changes["updated"][card_name][store] = {
                            "new": [listing for listing in new_listings if listing not in old_listings],
                            "removed": [listing for listing in old_listings if listing not in new_listings],
                            "changed": [
                                {
                                    "old": old_listing,
                                    "new": new_listing
                                }
                                for old_listing in old_listings
                                for new_listing in new_listings
                                if old_listing["condition"] == new_listing["condition"]
                                   and old_listing["set"] == new_listing["set"]
                                   and old_listing["finish"] == new_listing["finish"]
                                   and old_listing != new_listing
                            ]
                        }

    # Update the current availability with the new state
    current_availability = availability_update

    return changes


def stringify(availability, changes=None):
    """
    Convert the availability dictionary into a human-readable string format.
    Optionally include detected changes if provided.
    """
    message = ""

    # Include changes if provided
    if changes:
        if changes["added"]:
            message += "Newly Added Cards:\n"
            message += stringify(changes["added"]) + "\n"

        if changes["removed"]:
            message += "Removed Cards:\n"
            for card_name in changes["removed"]:
                message += f"{card_name} is no longer available.\n"
            message += "\n"

        if changes["updated"]:
            message += "Updated Cards:\n"
            for card_name, updates in changes["updated"].items():
                message += f"{card_name} has updates:\n"
                for store, store_changes in updates.items():
                    message += f"\t{store.store_name}:\n"
                    for listing in store_changes.get("new", []):
                        message += (
                            f"\t\tNew listing: {listing['stock']} in {listing['condition']} condition from "
                            f"the {listing['set']} set for {listing['price']} with a {listing['finish']} finish\n"
                        )
                    for listing in store_changes.get("removed", []):
                        message += (
                            f"\t\tRemoved listing: {listing['stock']} in {listing['condition']} condition from "
                            f"the {listing['set']} set for {listing['price']} with a {listing['finish']} finish\n"
                        )
                    for change in store_changes.get("changed", []):
                        old, new = change["old"], change["new"]
                        message += (
                            f"\t\tUpdated listing: Stock changed from {old['stock']} to {new['stock']}, "
                            f"price changed from {old['price']} to {new['price']}\n"
                        )
            message += "\n"

    # Include full availability
    if availability:
        message += "Current availability:\n"
        for card_name, stores in availability.items():
            message += f"{card_name} is available!\n"
            for store, listings in stores.items():
                message += f"\t{store.store_name} has {len(listings)} versions available\n"
                for listing in listings:
                    message += (
                        f"\t\t{listing['stock']} in {listing['condition']} condition from "
                        f"the {listing['set']} set for {listing['price']} with a {listing['finish']} finish\n"
                    )
            message += "\n"

    return message


### 🔹 availability State Management ###
def load_availability_state(username):
    """Loads availability state for a user."""
    availability = {}

    user_data = get_user(username)
    selected_stores = user_data.get("selected_stores", [])

    wanted_cards = {card["card_name"] for card in load_card_list(username)}

    for store in selected_stores:
        store_data = load_store_availability(store)

    for card_name, card_data in store_data.items():
        if card_name in wanted_cards:
                        if card_name not in availability:
                            availability[card_name] = {}
                        availability[card_name][store_name] = card_data["listings"]
    
    redis_key = f"{username}_availability_results"
    redis_data = redis_conn.hgetall(redis_key)

    for redis_entry, json_data in redis_data.items():
        try:
            store_name, card_name = redis_entry.split("_", 1)
            listings = json.loads(json_data)

            if store_name in selected_stores and card_name in wanted_cards:
                if card_name not in availability:
                    availability[card_name] = {}
                availability[card_name][store_name] = listings

        except ValueError as e:
            print(f"❌ Error processing Redis entry `{redis_entry}`: {e}")

    return availability

def save_availability_state(username, availability):
    """Saves availability state for a user."""
    save_json(availability, os.path.join(get_user_directory(username), "availability.json"))