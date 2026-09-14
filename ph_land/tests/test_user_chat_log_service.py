import json
from types import SimpleNamespace
from datetime import datetime
from pathlib import Path

import app.utils.user_chat_log_service as ulog
from app.llm.core.llm_lead_capture import Lead, save_lead


def test_save_lead_records_session_id(tmp_path, monkeypatch):
    leads_path = tmp_path / "leads.json"
    monkeypatch.setattr("app.llm.core.llm_lead_capture.LEADS_FILE_PATH", leads_path)

    lead = Lead(
        name="Alice",
        contact="555-1234",
        service_interest="wedding",
        ready_to_book=True,
    )

    save_lead(lead, session_id="session-123")

    data = json.loads(leads_path.read_text(encoding="utf-8").strip())
    assert data["capturedInSessionId"] == "session-123"


def test_save_lead_creates_missing_parent_directory(tmp_path, monkeypatch):
    leads_path = tmp_path / "nested" / "dir" / "leads.jsonl"
    monkeypatch.setattr("app.llm.core.llm_lead_capture.LEADS_FILE_PATH", leads_path)

    lead = Lead(
        name="Bob",
        contact="555-5678",
        service_interest="portrait",
        ready_to_book=True,
    )

    save_lead(lead)

    assert leads_path.exists()
    assert json.loads(leads_path.read_text(encoding="utf-8").strip())["name"] == "Bob"


def test_write_and_append(tmp_path):
    # Redirect logs directory to a temporary path
    ulog.CHAT_LOGS_DIR = tmp_path
    ulog.ensure_logs_dir()

    # initial session with one full user->assistant pair
    sess = SimpleNamespace(
        session_id="test-sess",
        created_at=datetime(2026, 8, 26, 5, 15, 24),
        history=[
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ],
    )

    ulog.write_session_log(sess)

    files = list(tmp_path.glob("log_test-sess_*.json"))
    assert len(files) == 1

    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert data == [{"userMessage": "hi", "llmAnswer": "hello"}]

    # append another pair to session history and write again
    sess.history += [
        {"role": "user", "content": "how are you?"},
        {"role": "assistant", "content": "I am fine"},
    ]

    ulog.write_session_log(sess)

    data2 = json.loads(files[0].read_text(encoding="utf-8"))
    assert data2 == [
        {"userMessage": "hi", "llmAnswer": "hello"},
        {"userMessage": "how are you?", "llmAnswer": "I am fine"},
    ]


def test_incomplete_pair_not_written(tmp_path):
    ulog.CHAT_LOGS_DIR = tmp_path
    ulog.ensure_logs_dir()

    sess = SimpleNamespace(
        session_id="incomplete",
        created_at=datetime(2026, 8, 26, 5, 15, 24),
        history=[{"role": "user", "content": "only user"}],
    )

    # should not create a log because there's no assistant reply yet
    ulog.write_session_log(sess)
    files = list(tmp_path.glob("log_incomplete_*.json"))
    assert len(files) == 0
