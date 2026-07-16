import os
from dotenv import load_dotenv

load_dotenv()

try:
    API_ID = int(os.environ.get("API_ID", "0"))
except ValueError:
    API_ID = 0

API_HASH = os.environ.get("API_HASH", "")
SESSION_NAME = os.environ.get("SESSION_NAME", "tg_resolver_session")

MIN_DELAY = float(os.environ.get("MIN_DELAY", "0.5"))
MAX_DELAY = float(os.environ.get("MAX_DELAY", "2.0"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))

if not API_ID or not API_HASH:
    raise ValueError("API_ID and API_HASH must be set in the .env file")
