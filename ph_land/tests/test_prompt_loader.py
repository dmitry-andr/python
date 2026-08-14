import os
from pathlib import Path

import pytest

from app.llm.core.prompt_loader import load_prompt, prompts_default_path


def test_load_prompt_prefers_workspace(tmp_path, monkeypatch):
    ws = tmp_path / "my_workspace"
    prompts = ws / "prompts"
    prompts.mkdir(parents=True)
    (prompts / "system.md").write_text("workspace system prompt")

    monkeypatch.setenv("WORKSPACE_FOLDER_PATH", str(ws))

    text = load_prompt("system.md")
    assert "workspace system prompt" in text


def test_load_prompt_falls_back_to_default(tmp_path, monkeypatch):
    # Ensure the workspace path does not exist
    monkeypatch.setenv("WORKSPACE_FOLDER_PATH", str(tmp_path / "no_such_workspace"))

    # Ensure default prompt exists
    default_file = prompts_default_path / "system.md"
    assert default_file.exists(), f"Expected default prompt at {default_file}"

    text = load_prompt("system.md")
    assert text is not None and len(text) > 0
