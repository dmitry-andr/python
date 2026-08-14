import os

from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


prompts_path = Path(os.getenv("WORKSPACE_FOLDER_PATH") + "/prompts").expanduser().resolve()
# Default to a top-level `prompts/` folder at the repository root
prompts_default_path = Path(__file__).resolve().parents[3] / "prompts"

def load_prompt(name: str) -> str:
    current_prompts_path = prompts_path
    if not current_prompts_path.exists():
        current_prompts_path = prompts_default_path
    return (current_prompts_path / name).read_text(encoding="utf-8")