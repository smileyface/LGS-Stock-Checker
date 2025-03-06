import json

from app.scryfall_api import fetch_scryfall_card_names

SCRYFALL_CARD_CACHE_KEY = "scryfall_card_names"
SCRYFALL_CARD_CACHE_EXPIRY = 86400

CARD_NAMES_CACHE = None  # Global cache variable

def initialize_cache(redis_client):
    """Initialize cache on app startup."""
    global CARD_NAMES_CACHE
    CARD_NAMES_CACHE = get_cached_card_names(redis_client)


def get_cached_card_names(redis_client):
    """Retrieve cached card names or fetch them if expired."""
    cached_data = redis_client.get(SCRYFALL_CARD_CACHE_KEY)
    if cached_data:
        print("✅ Loaded card names from cache.")
        return json.loads(cached_data)
    else:
        card_names = fetch_scryfall_card_names()
        if card_names:
            redis_client.setex(SCRYFALL_CARD_CACHE_KEY, SCRYFALL_CARD_CACHE_EXPIRY, json.dumps(card_names))
        else:
            print("⚠️ Warning: Returning an empty list because Scryfall fetch failed.")

        return card_names or []  # Always return a valid list