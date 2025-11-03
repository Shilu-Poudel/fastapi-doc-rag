from fastapi.testclient import TestClient
from app.main import app
from app.schemas.rag import ChatRequest, ChatResponse


client = TestClient(app)

def test_chat_success():
    response = client.post(
        "/api/v1/chat",
        json={"query": "What is the capital of France?"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), ChatResponse)

def test_chat_empty_query():
    response = client.post(
        "/api/v1/chat",
        json={"query": ""}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Query cannot be empty."

def test_chat_invalid_data():
    response = client.post(
        "/api/v1/chat",
        json={"invalid_field": "Some value"}
    )
    assert response.status_code == 422

def test_chat_memory_management():
    # Simulate a conversation
    client.post("/api/v1/chat", json={"query": "Tell me about FastAPI."})
    response = client.post("/api/v1/chat", json={"query": "What else?"})
    assert response.status_code == 200
    assert "FastAPI" in response.json()["response"]  # Assuming the response contains relevant context.