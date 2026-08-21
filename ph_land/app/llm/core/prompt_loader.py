import os

from dotenv import load_dotenv
from pathlib import Path

from app.utils.config import DEFAULT_WORKSPACE_FOLDER_PATH

load_dotenv()


# Build prompts path from optional environment override. If the env var is
# not set, leave `prompts_path` as a Path that will not exist so the loader
# falls back to `prompts_default_path` below.
_workspace_env = os.getenv("WORKSPACE_FOLDER_PATH")
if _workspace_env:
    prompts_path = (Path(_workspace_env).expanduser().resolve() / "prompts")
else:
    prompts_path = Path()  # empty/unset => won't exist

# Default to a top-level `prompts/` folder at the repository root
prompts_default_path = Path(DEFAULT_WORKSPACE_FOLDER_PATH) / "prompts"

def load_prompt(name: str) -> str:
    # Prefer prompts_path (workspace override). If the specific prompt
    # file is not present there, fall back to prompts_default_path.
    prompt_file = prompts_path / name
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")

    default_file = prompts_default_path / name
    if default_file.exists():
        return default_file.read_text(encoding="utf-8")

    raise FileNotFoundError(
        f"Prompt '{name}' not found in {prompts_path!s} or {prompts_default_path!s}"
    )