"""Global settings and shared constants for the application."""

from pathlib import Path

# Business and model config moved from app/config.py
BUSINESS_NAME = "Aperture Lane Photography"

BASE_DIR = Path(__file__).resolve().parent.parent.parent

APP_NAME = "ph_land"
APP_VERSION = "0.1.0"

DATA_DIR = BASE_DIR / "data"
SESSIONS_FILE = DATA_DIR / "sessions.json"
ORDERS_FILE = DATA_DIR / "orders.json"
LEADS_FILE_PATH = DATA_DIR / "leads.json"
DEFAULT_WORKSPACE_FOLDER_PATH = BASE_DIR / "app/llm/workspace"

VECTOR_DB_DIR = DATA_DIR / "chroma_db"

STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"
FAVICON_PATH = STATIC_DIR / "favicon.ico"

MAX_HISTORY_TURNS = 10
MEANINGLESS_THRESHOLD = 5
JSON_INDENT = 2

# Model choice: keep this cheap and low-temperature for a support bot.
MAIN_OPENAI_LLM_MODEL = "gpt-4.1-mini"
EMBEDDING_OPENAI_MODEL = "text-embedding-3-small"
SECONDARY_OPENAI_LLM_MODEL = "gpt-4.1-nano"
OPENAI_TEMPERATURE = 0.3



SERVICES = {
	"wedding": {
		"label": "Wedding Photography",
		"description": "Full-day and half-day wedding coverage, engagement sessions, albums.",
		"doc_file": "wedding_photography.md",
	},
	"portrait": {
		"label": "Portrait Photography",
		"description": "Individual, couple, family, and corporate headshot sessions, in-studio or on location.",
		"doc_file": "portrait_photography.md",
	},
	"studio_other": {
		"label": "Studio Rental & Other Professional Photography",
		"description": "Studio space rental, product photography, event coverage, real estate/interior photography.",
		"doc_file": "studio_and_other_services.md",
	},
}
