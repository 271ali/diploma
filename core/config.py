import os
from dotenv import load_dotenv

load_dotenv()

TELETHON_API_HASH = os.getenv("TELETHON_API_HASH",str)
TELETHON_API_ID = os.getenv("TELETHON_API_ID",int)
BOT_API=os.getenv("BOT_ID",str)
BASE_URL=os.getenv("BASE_URL",str)