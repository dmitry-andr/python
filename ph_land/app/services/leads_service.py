import json

from app.utils.config import CHAT_LOGS_DIR, LEADS_FILE_PATH


def load_leads():
    """Load all leads from the lead log file."""
    if not LEADS_FILE_PATH.exists():
        return []

    leads = []
    with open(LEADS_FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            leads.append(payload)
    return leads


def load_session_history_for_lead(lead: dict | None):
    """Return the latest chat history block associated with a lead's session."""
    if not lead:
        return []

    session_id = None
    for key in ("captured_in_session_id", "capturedInSessionId", "session_id", "sessionId"):
        session_id = lead.get(key)
        if session_id:
            break

    if not session_id:
        return []

    matches = sorted(CHAT_LOGS_DIR.glob(f"log_{session_id}_*.json"))
    if not matches:
        return []

    latest_log = matches[-1]
    try:
        history = json.loads(latest_log.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(history, list):
        return []

    entries = []
    for item in history:
        if not isinstance(item, dict):
            continue
        user_message = item.get("userMessage") or item.get("user_message") or ""
        llm_answer = item.get("llmAnswer") or item.get("llm_answer") or ""
        if user_message or llm_answer:
            entries.append({"userMessage": user_message, "llmAnswer": llm_answer})

    return entries
