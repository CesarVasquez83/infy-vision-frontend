from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

ALPHA_KPIS_PATH = DATA_DIR / "alpha_kpis.csv"
SERVICE_NAME = "infy-vision-local"