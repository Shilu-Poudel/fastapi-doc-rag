from typing import Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.vectorstore import VectorStore
from app.utils.redis_memory import RedisMemory
from app.services.booking_handler import BookingHandler
from app.services.embeddings import EmbeddingService
from app.services.booking_handler import BookingResult

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str
    query: str
    top_k: int = 5

class ChatResponse(BaseModel):
    reply: str

@router.post("", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    """
    Conversational RAG endpoint.
    - Retrieve relevant chunks from vector DB
    - Compose prompt with conversation memory
    - Call Groq LLM and return response
    - Save conversation in Redis
    """
    vs = VectorStore()
    emb = EmbeddingService()
    mem = RedisMemory()

    # Booking detection - simple heuristic / entity extraction
    booking = BookingHandler()
    if booking.detect_booking_intent(payload.query):
        booking_info = booking.extract_booking_details(payload.query)
        if booking_info:
            saved = booking.save_booking(booking_info)
            # create confirmation text
            confirmation = f"Booking confirmed for {saved.name} at {saved.date} {saved.time} (id: {saved.id})."
            # persist chat
            await mem.append_message(payload.user_id, {"role": "user", "content": payload.query})
            await mem.append_message(payload.user_id, {"role": "assistant", "content": confirmation})
            return ChatResponse(reply=confirmation)

    # embed the query for similarity search
    query_emb = emb.embed_text(payload.query)
    results = vs.search_vector(query_emb, top_k=payload.top_k)

    context_parts = [r["payload"].get("text", "") for r in results]
    context = "\n\n---\n\n".join(context_parts)

    # load conversation history from Redis
    history = await mem.get_messages(payload.user_id)

    # prepare prompt
    prompt = (
        "You are a helpful assistant that answers questions using the provided context.\n"
        "If the context does not contain the answer, say you don’t know.\n"
        "Use prior conversation memory to maintain continuity.\n\n"
        f"Context:\n{context}\n\n"
        f"Conversation history:\n{history}\n\n"
        f"User: {payload.query}\nAssistant:"
    )

    # call LLM (Groq)
    from app.services.embeddings import call_groq_completion
    reply = call_groq_completion(prompt)

    # save messages
    await mem.append_message(payload.user_id, {"role": "user", "content": payload.query})
    await mem.append_message(payload.user_id, {"role": "assistant", "content": reply})

    return ChatResponse(reply=reply)