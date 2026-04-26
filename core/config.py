import os
from typing import Type

from dotenv import load_dotenv

load_dotenv()

TELETHON_API_HASH = os.getenv("TELETHON_API_HASH",str)
TELETHON_API_ID = os.getenv("TELETHON_API_ID",int)

BASE_URL=os.getenv("BASE_URL",str)

SECRET_KEY=os.getenv("SECRET_KEY",str)
ALGORITHM =os.getenv("ALGORITHM",str)

ENCRYPTION_KEY=os.getenv("ENCRYPTION_KEY",str)
