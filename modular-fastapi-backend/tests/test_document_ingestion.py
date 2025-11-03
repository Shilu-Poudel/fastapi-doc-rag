from fastapi.testclient import TestClient
from app.main import app
from app.schemas.document import DocumentCreate

client = TestClient(app)

def test_ingest_document():
    file_content = b"Sample document content for testing."
    response = client.post(
        "/api/v1/ingest",
        files={"file": ("test_document.txt", file_content)},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Document ingested successfully"}

def test_ingest_invalid_file():
    response = client.post(
        "/api/v1/ingest",
        files={"file": ("test_document.txt", b"")},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid file content"}