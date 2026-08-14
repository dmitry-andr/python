from typing import List, Optional

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.utils.config import CHAT_MODEL, TEMPERATURE
from app.llm.core.llm_message_category_classifier import classify_message
from app.llm.core.prompt_loader import load_prompt
from app.llm.rag.rag_retriever import get_retriever
from app.utils.user_session_store import MAX_HISTORY_TURNS, MEANINGLESS_THRESHOLD, session_store


# switch to another model
# from langchain_ollama import ChatOllama
# self.llm = ChatOllama(model="llama3.1")


_retriever = None


class _SafeRetriever:
    def get_relevant_documents(self, query: str):
        return []

    def retrieve(self, query: str):
        return []


def _get_or_create_retriever(k: int = 4):
    global _retriever
    if _retriever is not None:
        return _retriever
    try:
        _retriever = get_retriever(k=k)
    except Exception as exc:
        print("Warning: RAG retriever initialization failed:", exc)
        _retriever = _SafeRetriever()
    return _retriever

# --------------------------------------------------------------------------
# LLM output schema
# --------------------------------------------------------------------------

class OfficeAdminResponse(BaseModel):
    """Structured output the LLM must return for every turn."""

    is_meaningful: bool = Field(
        description=(
            "True if the user's message is a coherent, meaningful question "
            "or request in natural language. False if it is random "
            "characters, keyboard mashing, a meaningless number/letter "
            "sequence, or otherwise not an actual question/request."
        )
    )
    reasoning: str = Field(
        description="One short sentence explaining the meaningfulness judgement."
    )
    answer: str = Field(
        description=(
            "The office administrator's reply to the user. If the message "
            "was not meaningful, this should be a brief, polite request for "
            "the user to rephrase or clarify what they need, in the same "
            "office-administrator persona."
        )
    )


# --------------------------------------------------------------------------
# Meaningless-message throttling
# --------------------------------------------------------------------------
 

 
BLOCKED_MESSAGE = (
    "It looks like I've had trouble understanding several of your recent "
    "messages. To keep things running smoothly, could you please take a "
    "short break and reach out again a bit later? Thanks for your "
    "patience!"
)


def _history_to_messages(history: List[dict]) -> list:
    """Convert stored {"role", "content"} dicts into LangChain message objects,
    trimmed to the most recent MAX_HISTORY_TURNS exchanges."""
    msgs = []
    for turn in history[-MAX_HISTORY_TURNS * 2 :]:
        if turn["role"] == "user":
            msgs.append(HumanMessage(content=turn["content"]))
        else:
            msgs.append(AIMessage(content=turn["content"]))
    return msgs

def _format_docs_for_rag(docs) -> str:
    return "\n\n---\n\n".join(d.page_content for d in docs)

class LLMService:

    def __init__(self):

        self.llm = ChatOpenAI(
            model=CHAT_MODEL,
            temperature=TEMPERATURE,
        )

        # Load system prompt from file
        self.system_prompt = load_prompt("system.md")

        # Create reusable prompt template
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                MessagesPlaceholder("history"),
                ("human", "{message}"),
            ]
        )

        structured_llm = self.llm.with_structured_output(OfficeAdminResponse)
        # Compose prompt + model into a chain
        self.chain = self.prompt | structured_llm

    def ask(self, message: str, session_id: Optional[str] = None) -> dict:
        """
        Run one turn of the conversation.

        - Looks up (or creates) the session for `session_id`.
        - Feeds that session's prior history into the chain for context.
        - Evaluates meaningfulness alongside the answer in a single LLM call.
        - Updates the session's running counters and appends this turn to
          its history.

        Returns a dict with the LLM response plus the session's up-to-date
        counters, so callers (e.g. a FastAPI route) don't need to reach into
        SESSIONS themselves.
        """
        session = session_store.get_or_create(session_id)

        if session.meaningless_messages >= MEANINGLESS_THRESHOLD:
            session = session_store.record_turn(
                session_id=session.session_id,
                user_message=message,
                assistant_answer=BLOCKED_MESSAGE,
                is_meaningful=False,
            )
            return {
                "session_id": session.session_id,
                "answer": BLOCKED_MESSAGE,
                "is_meaningful": False,
                "reasoning": (
                    f"Session exceeded {MEANINGLESS_THRESHOLD} meaningless "
                    "messages; LLM call skipped."
                ),
                "llm_called": False,
                "blocked": True,
                "total_messages": session.total_messages,
                "meaningful_messages": session.meaningful_messages,
                "meaningless_messages": session.meaningless_messages,
            }

        category = classify_message(message, _history_to_messages(session.history))

        # Retrieve relevant documents from the local RAG vectorstore and
        # include them in the prompt so the LLM can ground its answer on
        # the business data stored in markdown files.
        docs = []
        try:
            retr = _get_or_create_retriever(k=4)
            if hasattr(retr, "get_relevant_documents"):
                docs = retr.get_relevant_documents(message)
            elif hasattr(retr, "retrieve"):
                docs = retr.retrieve(message)
        except Exception as e:
            print("RAG retrieval failed:", e)

        if docs:
            augmented_message = (
                "Context from knowledge base:\n" + _format_docs_for_rag(docs) + "\n\n" + message
            )
        else:
            augmented_message = message

        response: OfficeAdminResponse = self.chain.invoke(
            {
                "message": augmented_message,
                "history": _history_to_messages(session.history),
            }
        )

        session = session_store.record_turn(
            session_id=session.session_id,
            user_message=message,
            assistant_answer=response.answer,
            is_meaningful=response.is_meaningful,
        )

        return {
            "session_id": session.session_id,
            "answer": response.answer,
            "is_meaningful": response.is_meaningful,
            "reasoning": response.reasoning,
            "total_messages": session.total_messages,
            "meaningful_messages": session.meaningful_messages,
            "meaningless_messages": session.meaningless_messages,
        }

    def get_session_stats(self, session_id: str) -> Optional[dict]:
        return session_store.get_stats(session_id)


llm_service = LLMService()