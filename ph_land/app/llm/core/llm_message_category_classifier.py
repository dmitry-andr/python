from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from app.llm.core.llm_factory import get_secondary_llm
from app.utils.config import BUSINESS_NAME, SERVICES
from app.llm.core.prompt_loader import load_prompt


VALID_CATEGORIES = (
    "service_question",
    "booking_request",
    "greeting_or_smalltalk",
    "off_topic",
)

def _get_router_chain():
    router_llm = get_secondary_llm()
    router_prompt = PromptTemplate.from_template(
        load_prompt("message_categorization.md")
    )
    return router_prompt | router_llm | StrOutputParser()


def classify_message(message: str, history: str) -> str:
    """
    Returns one of VALID_CATEGORIES. Falls back to 'service_question' on any
    unexpected output so a parsing hiccup routes to the safest default rather
    than silently going off-topic or blocking the user.
    """
    router_chain = _get_router_chain()
    raw = router_chain.invoke(
        {
            "business_name": BUSINESS_NAME,
            "services_list": ", ".join(service["label"] for service in SERVICES.values()),
            "message": message,
            "history": history,
        }
    ).strip().lower()
    for category in VALID_CATEGORIES:
        if category in raw:
            return category
    return "service_question"
