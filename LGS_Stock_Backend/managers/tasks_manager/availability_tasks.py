import managers.store_manager as store_manager
from managers import availability_manager
from managers.socket_manager import socket_emit
from utility import logger


def update_availability_single_card(username, store_name, card):
    """Background task to update the availability for a single card at a store.
    """
    # Validate store_name
    if not store_name:
        logger.warning(f"🚨 Invalid store name: {store_name}. Task aborted.")
        return False

    card_name = card.get("card_name")
    if not card_name:
        logger.error(f"❌ Task received card data without a 'card_name'. Aborting. Data: {card}")
        return False

    logger.info(f"📌 Task started: Updating availability for {card_name} at {store_name} (User: {username})")

    # Ensure store_name is in the correct format
    store = store_manager.store_list(store_name)
    if not store:
        logger.warning(f"🚨 Store '{store_name}' is not configured or missing from STORE_REGISTRY. Task aborted.")
        return False

    logger.info(f"🔍 Checking availability for {card_name} at {store_name}")

    # Fetch availability using the specific store's implementation
    card_specs = card.get("specifications")
    available_items = store.fetch_card_availability(card_name, card_specs)

    if available_items:
        logger.info(f"✅ Found {len(available_items)} listings for {card_name} at {store_name}. Caching and emitting.")
        
        # 1. Cache the results first for data integrity.
        availability_manager.cache_availability_data(store_name, card_name, available_items)
        logger.info(f"✅ Cached availability results for {card_name} at {store_name}.")

        # 2. Use the dedicated worker-safe emit function from socket_emit.
        event_data = {"username": username, "store": store_name, "card": card_name, "items": available_items}
        socket_emit.emit_from_worker("card_availability_data", event_data, room=username)
    else:
        logger.warning(f"⚠️ No available listings found for {card_name} at {store_name}. Moving on.")

    return True
