from fastapi import APIRouter, HTTPException
from langgraph.errors import GraphRecursionError

from app.core.config import settings
from app.core.logging import logger
from app.schemas.rag import ChatRequest, ChatResponse
from app.services.agent import get_agent
from app.services.memory import ConversationMemory

router = APIRouter()
memory = ConversationMemory()


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    """Answer a user query through the tool-using RAG agent with memory."""
    history = memory.load(payload.user_id)
    messages = history + [{"role": "user", "content": payload.query}]

    try:
        result = await get_agent().ainvoke(
            {"messages": messages},
            config={"recursion_limit": settings.agent_recursion_limit},
        )
    except GraphRecursionError:
        logger.warning("Agent hit recursion limit for user %s", payload.user_id)
        raise HTTPException(
            status_code=503,
            detail="The assistant could not complete the request. Please rephrase and try again.",
        )
    except Exception:
        logger.exception("Chat request failed for user %s", payload.user_id)
        raise HTTPException(
            status_code=503, detail="Chat service is temporarily unavailable."
        )

    answer = result["messages"][-1].content
    memory.append(payload.user_id, "user", payload.query)
    memory.append(payload.user_id, "assistant", answer)

    return ChatResponse(user_id=payload.user_id, response=answer)
