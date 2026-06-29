import os
from pathlib import Path
from dotenv import load_dotenv

# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================
load_dotenv()

# =========================================================
# PROJECT DIRECTORIES
# =========================================================
BASE_DIR = Path(__file__).resolve().parent

SRC_DIR = BASE_DIR / "src"
DB_DIR = SRC_DIR / "db"
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"

# Create required folders automatically if missing
SRC_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================
# EUMETSAT / METEOSAT SETTINGS
# =========================================================
EUMETSAT_CONSUMER_KEY = os.getenv("EUMETSAT_CONSUMER_KEY")
EUMETSAT_CONSUMER_SECRET = os.getenv("EUMETSAT_CONSUMER_SECRET")

# MTG Active Fire Monitoring collection
EUM_COLLECTION = os.getenv("EUM_COLLECTION", "EO:EUM:DAT:0682")

# =========================================================
# NASA FIRMS / VIIRS SETTINGS
# =========================================================
FIRMS_MAP_KEY = os.getenv("FIRMS_MAP_KEY")

# =========================================================
# FILE PATHS
# =========================================================
AOI_FILE = os.getenv("AOI_FILE", str(SRC_DIR / "aoi.geojson"))
DB_FILE = os.getenv("DB_FILE", str(DB_DIR / "alerts.db"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", str(DEFAULT_OUTPUT_DIR))

# Make sure output directory exists
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# =========================================================
# FIRE DETECTION SETTINGS
# =========================================================
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.5"))
LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS", "2"))

# 900 seconds = 15 minutes
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "900"))

# =========================================================
# TELERIVET SMS ALERT SETTINGS
# =========================================================
TELERIVET_API_KEY = os.getenv("TELERIVET_API_KEY")
TELERIVET_PROJECT_ID = os.getenv("TELERIVET_PROJECT_ID")
TELERIVET_GROUP_ID = os.getenv("TELERIVET_GROUP_ID")

# Optional single phone number fallback
ALERT_TO = os.getenv("ALERT_TO")

# =========================================================
# BASIC VALIDATION
# =========================================================
def check_required_settings():
    missing = []

    required = {
        "EUMETSAT_CONSUMER_KEY": EUMETSAT_CONSUMER_KEY,
        "EUMETSAT_CONSUMER_SECRET": EUMETSAT_CONSUMER_SECRET,
        "FIRMS_MAP_KEY": FIRMS_MAP_KEY,
    }

    for key, value in required.items():
        if not value:
            missing.append(key)

    if missing:
        raise ValueError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Please check your .env file."
        )