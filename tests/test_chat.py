from fastapi.testclient import TestClient


def test_rejects_empty_query(client: TestClient) -> None:
    response = client.post("/api/v1/chat", json={"user_id": "u1", "query": ""})
    assert response.status_code == 422


def test_rejects_missing_fields(client: TestClient) -> None:
    response = client.post("/api/v1/chat", json={"query": "hello"})
    assert response.status_code == 422
