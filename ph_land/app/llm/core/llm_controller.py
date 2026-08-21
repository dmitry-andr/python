from typing import Optional
from app.llm.core.llm_lead_capture import maybe_capture_lead
from app.llm.core.llm_message_category_classifier import classify_message
from app.llm.core.llm_chat import llm_service
from app.utils.user_session_store import session_store
from app.llm.core.llm_chat import _history_to_messages


def process_user_input(message: str, session_id: Optional[str] = None) -> dict:

    session = session_store.get_or_create(session_id)

    history_text = _history_to_messages(session.history)
    category = classify_message(message, history_text)

    if category == "off_topic":
        print("Off topic")

    if category == "booking_request":
        print("Booking request")
        capture_result = maybe_capture_lead(message, history_text, session.session_id)
        if capture_result is not None:
            return capture_result

    # service_question or greeting_or_smalltalk
    print("Service question or greeting/smalltalk")
    llm_response = llm_service.ask(message, session_id)
    return llm_response


    
        