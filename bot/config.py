import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "bot" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "0").strip()
ADMIN_IDS = set()
for part in ADMIN_ID_RAW.split(","):
    part = part.strip()
    if part.lstrip("-").isdigit():
        ADMIN_IDS.add(int(part))
ADMIN_ID = list(ADMIN_IDS)[0] if ADMIN_IDS else 0
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot/data/bot.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
REWARD_AMOUNT = float(os.getenv("REWARD_AMOUNT", "2.0"))
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "").strip()
REQUIRED_CHANNEL_URL = os.getenv("REQUIRED_CHANNEL_URL", "").strip()

