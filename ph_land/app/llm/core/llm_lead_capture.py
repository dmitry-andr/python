import json
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field
from app.llm.core import prompt_loader
from app.llm.core.llm_factory import get_secondary_llm
from app.utils.config import LEADS_FILE_PATH, SERVICES
from app.utils.user_session_store import session_store


class Lead(BaseModel):
    """Structured booking/lead info pulled from the conversation."""

    name: Optional[str] = Field(None, description="Customer's name, if given")
    contact: Optional[str] = Field(
        None, description="Phone number or email, if given"
    )
    service_interest: Optional[
        Literal["wedding", "portrait", "studio_other", "unclear"]
    ] = Field(None, description="Which of the 3 services they're interested in")
    preferred_date: Optional[str] = Field(
        None, description="Preferred date/timeframe, if mentioned, as free text"
    )
    location_or_notes: Optional[str] = Field(
        None, description="Venue/location, event type, or other relevant detail"
    )
    ready_to_book: bool = Field(
        False, description="True if the user has clearly asked to book/get a quote"
    )


def extract_lead(history_text: str) -> Lead:
    """Runs a structured-output LLM call to pull booking info out of the chat so far."""
    llm = get_secondary_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(Lead)
    prompt = prompt_loader.load_prompt("lead_extraction_prompt.md").format(history=history_text)
    return structured_llm.invoke(prompt)


def save_lead(lead: Lead) -> str:
    """
    Persists a lead. This is a stand-in for a real integration --
    swap this out for a CRM API call, a Google Sheets append, or a DB insert.
    """
    record = lead.model_dump()
    record["captured_at"] = datetime.utcnow().isoformat()
    if record.get("service_interest") in SERVICES:
        record["service_label"] = SERVICES[record["service_interest"]]["label"]

    with open(LEADS_FILE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return (
        "Thanks! I've noted your details and someone from our team will follow up "
        "shortly to confirm availability and finalize the booking."
    )


def maybe_capture_lead(message: str, history_text: str, session_id: Optional[str] = None) -> Optional[dict]:
    """
    Called on 'booking_request' turns. Extracts what we can from the conversation
    and, if the user seems ready to book, saves the lead and returns a confirmation
    message to show the user. Returns None if not enough info / not ready yet.
    """
    # Defensive: callers sometimes pass the chat history as a list of message
    # objects (e.g. LangChain `HumanMessage`) or strings. Convert each entry
    # into a readable line before joining.
    if isinstance(history_text, list):
        def _msg_to_line(item):
            if isinstance(item, str):
                return item
            content = getattr(item, "content", None)
            role = getattr(item, "type", None) or getattr(item, "role", None)
            if not role and hasattr(item, "__class__"):
                role = item.__class__.__name__.replace("Message", "")
            role_label = str(role).capitalize() if role else "Message"
            if content is None:
                return f"{role_label}: {str(item)}"
            return f"{role_label}: {content}"

        history_text = "\n".join(_msg_to_line(m) for m in history_text)
    if history_text is None:
        history_text = ""
    # Also ensure message is a string
    if not isinstance(message, str):
        message = str(message)

    # Avoid duplicating the user's message in the history: if the last
    # line of `history_text` already equals the `User: ...` line, don't append.
    user_line = f"User: {message}"
    last_line = history_text.strip().splitlines()[-1] if history_text.strip() else ""
    if last_line == user_line:
        history_for_prompt = history_text
    else:
        history_for_prompt = (history_text + "\n" + user_line) if history_text else user_line

    lead = extract_lead(history_for_prompt)

    if lead.ready_to_book and lead.contact:
        confirmation = save_lead(lead)
        session = session_store.record_turn(
            session_id=session_id,
            user_message=message,
            assistant_answer=confirmation,
            is_meaningful=True,
        )
        return {
            "session_id": session.session_id,
            "answer": confirmation,
            "is_meaningful": True,
            "reasoning": "Captured lead and saved.",
            "total_messages": session.total_messages,
            "meaningful_messages": session.meaningful_messages,
            "meaningless_messages": session.meaningless_messages,
        }

    missing = []
    if not lead.name:
        missing.append("your name")
    if not lead.contact:
        missing.append("a phone number or email")
    if not lead.service_interest or lead.service_interest == "unclear":
        missing.append("which service you're interested in")

    if missing:
        #prompt = "Happy to get that booked! Could you share " + ", ".join(missing) + "?"
        prompt = "Happy to get that booked! Could you share " + missing[0] + "?"
        session = session_store.record_turn(
            session_id=session_id,
            user_message=message,
            assistant_answer=prompt,
            is_meaningful=True,
        )
        return {
            "session_id": session.session_id,
            "answer": prompt,
            "is_meaningful": True,
            "reasoning": "Asked user for missing booking details.",
            "total_messages": session.total_messages,
            "meaningful_messages": session.meaningful_messages,
            "meaningless_messages": session.meaningless_messages,
        }

    return None
