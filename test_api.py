import pytest
from fastapi.testclient import TestClient
from main import app  # Assuming your FastAPI app is in 'main.py'

client = TestClient(app)

# Helper function to get a valid token
def get_valid_token():
    # Assuming you have an endpoint for token generation (e.g., /token) to get JWT
    response = client.post("/token", data={"username": "test_user", "password": "test_pass"})
    return response.json().get("access_token")

# Test Ingestion Endpoint
def test_ingest_document():
    with open("test_document.txt", "w") as f:
        f.write("This is a test document for ingestion.")
    
    with open("test_document.txt", "rb") as f:
        response = client.post("/ingest/", files={"file": f})
    
    assert response.status_code == 200
    assert "message" in response.json()
    assert "document_id" in response.json()

# Test Query API with valid token
def test_query_qa_with_valid_token():
    query_data = {
        "question": "What is the test document about?",
        "document_ids": [1]  # Assuming document ID 1 exists
    }
    token = get_valid_token()  # Get a valid JWT token
    
    response = client.post(
        "/query/", 
        json=query_data, 
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert "question" in response.json()
    assert "answer" in response.json()

# Test Query API without token (authentication failure)
def test_query_qa_without_token():
    query_data = {
        "question": "What is the test document about?",
        "document_ids": [1]
    }
    response = client.post("/query/", json=query_data)
    
    assert response.status_code == 401  # Unauthorized

# Test List Documents API with valid token
def test_list_documents_with_valid_token():
    token = get_valid_token()  # Get a valid JWT token
    response = client.get("/documents/", headers={"Authorization": f"Bearer {token}"})
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

# Test List Documents API without token (authentication failure)
def test_list_documents_without_token():
    response = client.get("/documents/")
    
    assert response.status_code == 401  # Unauthorized

# Test Rate Limiting on Ingestion
def test_ingest_document_rate_limiting():
    with open("test_document.txt", "w") as f:
        f.write("This is a test document for rate limiting.")
    
    with open("test_document.txt", "rb") as f:
        # Simulating hitting the rate limit
        for _ in range(6):  # Assuming the rate limit is 5 per minute
            response = client.post("/ingest/", files={"file": f})
    
    assert response.status_code == 429  # Too Many Requests
