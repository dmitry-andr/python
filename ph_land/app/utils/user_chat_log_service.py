from pathlib import Path
import json
from datetime import datetime
from typing import Any

from app.utils.config import CHAT_LOGS_DIR
import logging


def ensure_logs_dir() -> None:
    try:
        CHAT_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        # best-effort; caller will handle failures if necessary
        pass


def write_session_log(session: Any) -> None:
    """Write a per-session log file pairing user messages with LLM answers.

    The file is named `log_<sessionId>_<session_createdAt>.json` and
    contains a JSON array of objects: {"userMessage": ..., "llmAnswer": ...}
    """
    try:
        # ensure logs dir exists before attempting to write
        ensure_logs_dir()

        entries = getattr(session, "history", []) or []
        pairs = []
        last_user = None
        for entry in entries:
            if isinstance(entry, dict):
                role = entry.get("role")
                content = entry.get("content")
            else:
                role = None
                content = None

            if role == "user":
                last_user = content
            elif role == "assistant":
                if last_user is not None:
                    pairs.append({"userMessage": last_user, "llmAnswer": content})
                    last_user = None

        created_at = getattr(session, "created_at", None)
        if created_at is None:
            created_at_str = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        else:
            created_at_str = created_at.strftime("%Y%m%dT%H%M%SZ")

        sid = getattr(session, "session_id", None) or getattr(session, "id", None) or "unknown"
        log_name = f"log_{sid}_{created_at_str}.json"
        log_path: Path = CHAT_LOGS_DIR / log_name

        # If there are no complete user->assistant pairs yet, do nothing
        if not pairs:
            return

        # Merge with existing file if present, appending only new pairs
        if log_path.exists():
            try:
                existing = json.loads(log_path.read_text(encoding="utf-8") or "[]")
                if not isinstance(existing, list):
                    existing = []
            except Exception:
                existing = []

            # find common prefix length
            i = 0
            while i < len(existing) and i < len(pairs) and existing[i] == pairs[i]:
                i += 1

            new_pairs = pairs[i:]
            if not new_pairs:
                return

            combined = existing + new_pairs
            log_path.write_text(json.dumps(combined, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            # file missing: write all pairs
            log_path.write_text(json.dumps(pairs, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as exc:
        logging.getLogger(__name__).warning(
            "Failed to write session log %s: %s", locals().get('log_path', '<unknown>'), exc
        )
        # best-effort: don't raise from logging
        return
