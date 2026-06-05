from fastapi.testclient import TestClient


def test_rejects_unsupported_file_type(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ingest",
        files={"file": ("notes.bin", b"data", "application/octet-stream")},
    )
    assert response.status_code == 400


def test_rejects_missing_file(client: TestClient) -> None:
    response = client.post("/api/v1/ingest")
    assert response.status_code == 422
