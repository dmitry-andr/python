"""Global settings and shared constants for the application."""

from pathlib import Path
import json
import os
import logging

# Business and model config moved from app/config.py
BUSINESS_NAME = "Aperture Lane Services"

BASE_DIR = Path(__file__).resolve().parent.parent.parent

APP_NAME = "ph_land"
APP_VERSION = "0.1.0"

RUNTIME_DATA_DIR = BASE_DIR / "runtime_data"
SESSIONS_FILE = RUNTIME_DATA_DIR / "chat_sessions/sessions.json"
CHAT_LOGS_DIR = RUNTIME_DATA_DIR / "chat_sessions/logs"
SERVICES_FILE = RUNTIME_DATA_DIR / "services.json"
ORDERS_FILE = RUNTIME_DATA_DIR / "orders.json"
CUSTOMERS_FILE = RUNTIME_DATA_DIR / "customers.json"
LEADS_FILE_PATH = RUNTIME_DATA_DIR / "leads.json"
DEFAULT_WORKSPACE_FOLDER_PATH = BASE_DIR / "app/llm/workspace"

VECTOR_DB_DIR = RUNTIME_DATA_DIR / "chroma_db"

STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
FAVICON_PATH = STATIC_DIR / "favicon.ico"

MAX_HISTORY_TURNS = 10
MEANINGLESS_THRESHOLD = 5
JSON_INDENT = 2

# Model choice: keep this cheap and low-temperature for formal tasks.
MAIN_OPENAI_LLM_MODEL = "gpt-4.1-mini"
EMBEDDING_OPENAI_MODEL = "text-embedding-3-small"
SECONDARY_OPENAI_LLM_MODEL = "gpt-4.1-nano"
OPENAI_TEMPERATURE = 0.3


# Determine workspace folder: prefer environment override, fall back to default.
_env_ws = os.environ.get("WORKSPACE_FOLDER_PATH")
if _env_ws:
	try:
		WORKSPACE_FOLDER_PATH = Path(_env_ws)
	except Exception:
		WORKSPACE_FOLDER_PATH = DEFAULT_WORKSPACE_FOLDER_PATH
else:
	WORKSPACE_FOLDER_PATH = DEFAULT_WORKSPACE_FOLDER_PATH

# Load services list from the resolved workspace folder. Prefer the
# `WORKSPACE_FOLDER_PATH` environment variable; if it's not set, use
# `DEFAULT_WORKSPACE_FOLDER_PATH`. Do NOT hardcode service values here.
_SERVICES_FILE = WORKSPACE_FOLDER_PATH / "services" / "services.json"

SERVICES = {}
if _SERVICES_FILE.exists():
	try:
		with open(_SERVICES_FILE, "r", encoding="utf-8") as f:
			SERVICES = json.load(f)
	except Exception as exc:
		logging.getLogger(__name__).warning(
			"Failed to parse services.json at %s: %s", _SERVICES_FILE, exc
		)
else:
	logging.getLogger(__name__).info(
		"No services.json found at %s; SERVICES will be empty.", _SERVICES_FILE
	)
