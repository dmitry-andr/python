import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from app.utils.config import BUSINESS_NAME, CHAT_MODEL, SERVICES
from app.llm.core.prompt_loader import load_prompt

load_dotenv()

VALID_CATEGORIES = (
    "service_question",
    "booking_request",
    "greeting_or_smalltalk",
    "off_topic",
)

def _get_router_chain():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Configure it in your environment or .env file before using the LLM."
        )

    router_llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)
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
