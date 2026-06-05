from functools import lru_cache

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.booking import create_booking
from app.services.embeddings import embed_text
from app.services.vectorstore import QdrantStore

SYSTEM_PROMPT = (
    "You are a helpful assistant for PalmMind. "
    "Use the retrieve_context tool to answer questions about ingested documents, "
    "and answer only from the retrieved context. If the answer is not in the "
    "context, say you do not know. When the user wants to book an interview, "
    "make sure you have their full name, email, date and time, then call "
    "book_interview to confirm it. Respond professionally and do not use emojis."
)


@tool
def retrieve_context(query: str) -> str:
    """Search the ingested document knowledge base for the given query."""
    hits = QdrantStore().search(embed_text(query), top_k=5)
    if not hits:
        return "No relevant context found."
    return "\n\n".join(hit["payload"].get("text", "") for hit in hits)


@tool
def book_interview(full_name: str, email: str, date: str, time: str) -> str:
    """Book an interview and email a confirmation.

    Requires full name, email, date (YYYY-MM-DD) and time (HH:MM).
    """
    db = SessionLocal()
    try:
        booking = create_booking(db, full_name, email, date, time)
    except ValueError as exc:
        return f"Could not book the interview: {exc}. Please ask the user to correct it."
    finally:
        db.close()
    return (
        f"Interview confirmed for {full_name} on {date} at {time}. "
        f"A confirmation email was sent to {email} (booking #{booking.id})."
    )


@lru_cache
def get_agent() -> CompiledStateGraph:
    model = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.groq_api_key,
        base_url=settings.groq_base_url,
        temperature=0.2,
    )
    return create_react_agent(
        model, tools=[retrieve_context, book_interview], prompt=SYSTEM_PROMPT
    )
