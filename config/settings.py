import os


SMTP_SERVER = "smtp.gmail.com"  # For Gmail
SMTP_PORT = 587
EMAIL_SENDER = "lgsbot.smileyface@gmail.com"  # Replace with your email
EMAIL_PASSWORD = "tfkmdssquntqhcxs"  # Replace with your email password
EMAIL_RECIPIENT = "kasonbennett65@gmail.com"  # Email to send notifications to


CHECK_INTERVAL = 1800  # Time in seconds (300 seconds = 5 minutes)

# Path to save state.json within the config package
STATE_FILE_PATH = os.path.join(os.path.dirname(__file__), "state.json")
CARD_LIST_FILE_PATH = os.path.join(os.path.dirname(__file__), "card_list.txt")

# API URL for Scryfall sets
SCRYFALL_SETS_API = "https://api.scryfall.com/sets"

# Path to save the set lookup table
SET_LOOKUP_FILE = os.path.join(os.path.dirname(__file__), "set_lookup.json")

# Interval for updating the set lookup table (24 hours = 86400 seconds)
SET_UPDATE_INTERVAL = 86400  # 24 hours