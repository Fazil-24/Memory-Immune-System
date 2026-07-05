import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")

DATASET_NAME = os.environ.get("DATASET_NAME", "compliance_brain")
DEMO_CORPUS_DIR = PROJECT_ROOT / "demo_corpus"

# On a persistent-disk host (e.g. Railway with a Volume mounted at /data),
# set SIDELAYER_DB_PATH to a path under that mount so status/confidence
# survives redeploys. Defaults to living next to the backend code for local
# dev, where that's not a concern.
SIDELAYER_DB_PATH = Path(os.environ.get("SIDELAYER_DB_PATH", str(BACKEND_DIR / "sidelayer.db")))
SIDELAYER_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DEMO_QUERY = "What is the current rule for EU customer data retention?"

os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")
