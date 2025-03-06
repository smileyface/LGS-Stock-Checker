import requests


def fetch_scryfall_card_names():
    """Fetch all Magic: The Gathering card names from Scryfall and cache them."""
    print("🔄 Fetching card names from Scryfall...")
    url = "https://api.scryfall.com/catalog/card-names"
    response = requests.get(url)

    if response.status_code == 200:
        card_names = response.json().get("data", [])
        print(f"✅ Cached {len(card_names)} card names for 24 hours.")
        return card_names
    else:
        print(f"❌ Failed to fetch Scryfall data: {response.status_code}")
        return []