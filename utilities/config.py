import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://dummypay.vercel.app"
TIMEOUT = 10000  # milliseconds

EMAIL = os.getenv("DUMMYPAY_EMAIL")
PASSWORD = os.getenv("DUMMYPAY_PASSWORD")
RECIPIENT_EMAIL = os.getenv("DUMMYPAY_RECIPIENT_EMAIL")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
