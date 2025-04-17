import pytest
from fastapi.testclient import TestClient
from main import app  # Assuming your FastAPI app is in 'main.py'

client = TestClient(app)

# Test Ingestion Endpoint
def test_ingest_document():
    with open("test_document.txt", "w") as f:
        f.write("This is a test document for ingestion.")
    
    with open("test_document.txt", "rb") as f:
        response = client.post("/ingest/", files={"file": f})
    
    assert response.status_code == 200
    assert "message" in response.json()
    assert "document_id" in response.json()

# Test Query API
def test_query_qa():
    query_data = {
        "question": "What is the test document about?",
        "document_ids": [1]  # Assuming document ID 1 exists
    }
    response = client.post("/query/", json=query_data)
    
    assert response.status_code == 200
    assert "question" in response.json()
    assert "answer" in response.json()

# Test List Documents API
def test_list_documents():
    response = client.get("/documents/")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0
