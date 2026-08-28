"""
File-backed session store.

Keeps track of each user's session: how many messages they've sent in
total, how many were judged meaningful vs. meaningless by the LLM, and
the recent conversation history used for context.

This is a simple JSON-file-backed replacement for the plain in-memory
`SESSIONS` dict — sessions now survive process restarts. It's still a
single-file, whole-file-read/write store, so it's meant for small/dev
workloads; swap for Redis or a real DB if you need concurrency at scale
or multiple app workers/replicas.
"""

import json
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from app.utils.config import MAX_HISTORY_TURNS, SESSIONS_FILE
from app.utils.user_chat_log_service import write_session_log


class SessionData(BaseModel):
    session_id: str
    created_at: datetime
    updated_at: datetime
    total_messages: int = 0
    meaningful_messages: int = 0
    meaningless_messages: int = 0
    history: List[dict] = Field(default_factory=list)  # [{"role": "...", "content": "..."}]

class SessionStore:
    """Thread-safe, JSON-file-backed store for SessionData objects."""

    def __init__(self, path: Path = SESSIONS_FILE):
        self._path = path
        self._lock = threading.Lock()
        self._sessions: Dict[str, SessionData] = {}
        # ensure the directory for the sessions file exists so writes don't fail
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            # best-effort: if we can't create the dir, let subsequent IO raise
            pass

        self._load()

    # -- persistence ------------------------------------------------------

    def _load(self) -> None:
        if not self._path.exists():
            self._sessions = {}
            return

        raw = json.loads(self._path.read_text(encoding="utf-8") or "{}")
        self._sessions = {
            sid: SessionData(**data) for sid, data in raw.items()
        }

    def _flush(self) -> None:
        serialisable = {
            sid: json.loads(session.model_dump_json())
            for sid, session in self._sessions.items()
        }
        self._path.write_text(
            json.dumps(serialisable, indent=2, default=str), encoding="utf-8"
        )

        # write per-session chat logs using the dedicated service (best-effort)
        for sid, session in self._sessions.items():
            try:
                write_session_log(session)
            except Exception:
                # do not fail on logging errors
                continue

    # -- public API ---------------------------------------------------------

    def get_or_create(self, session_id: Optional[str]) -> SessionData:
        with self._lock:
            if session_id and session_id in self._sessions:
                return self._sessions[session_id]

            now = datetime.utcnow()
            new_id = session_id or str(uuid.uuid4())
            session = SessionData(session_id=new_id, created_at=now, updated_at=now)
            self._sessions[new_id] = session
            self._flush()
            return session

    def record_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_answer: str,
        is_meaningful: bool,
    ) -> SessionData:
        """Update counters + history for one exchange and persist to disk."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise KeyError(f"Unknown session_id: {session_id}")

            session.total_messages += 1
            if is_meaningful:
                session.meaningful_messages += 1
            else:
                session.meaningless_messages += 1

            session.history.append({"role": "user", "content": user_message})
            session.history.append({"role": "assistant", "content": assistant_answer})
            # keep only the most recent turns
            session.history = session.history[-MAX_HISTORY_TURNS * 2 :]

            session.updated_at = datetime.utcnow()

            self._flush()
            return session

    def get(self, session_id: str) -> Optional[SessionData]:
        with self._lock:
            return self._sessions.get(session_id)

    def get_stats(self, session_id: str) -> Optional[dict]:
        session = self.get(session_id)
        if session is None:
            return None
        return {
            "session_id": session.session_id,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "total_messages": session.total_messages,
            "meaningful_messages": session.meaningful_messages,
            "meaningless_messages": session.meaningless_messages,
        }

    def list_sessions(self) -> List[str]:
        with self._lock:
            return list(self._sessions.keys())


# Module-level singleton, mirroring how `llm_service` is used elsewhere.
session_store = SessionStore()