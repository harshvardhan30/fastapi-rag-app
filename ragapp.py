from fastapi import FastAPI, UploadFile, File, Request, Depends
from typing import List, Dict
from langchain.embeddings import OllamaEmbeddings
from langchain.vectorstores.pgvector import PGVector
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import Ollama
from langchain.chains import RetrievalQA
import asyncpg
import json
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.security import OAuth2PasswordBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime
import jwt

app = FastAPI()

# --- CONFIGURATION ---
DATABASE_CONFIG = {
    "dbname": "rag_db",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432"
}
DATABASE_URL = f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['dbname']}"

# --- EMBEDDING MODEL ---
embedding_model = OllamaEmbeddings(model="llama3:8b")

# --- DB CONNECTION ---
async def get_db_connection():
    return await asyncpg.connect(DATABASE_URL)

# --- INIT PGVector VECTOR STORE ---
def get_vector_store():
    return PGVector(
        embedding_function=embedding_model,
        collection_name="rag_chunks",
        connection_string=DATABASE_URL
    )

# --- RATE LIMITING SETUP ---
limiter = Limiter(key_func=get_remote_address)

# --- AUTHENTICATION SETUP ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- PROMETHEUS SETUP ---
instrumentator = Instrumentator()

@app.on_event("startup")
async def startup():
    instrumentator.instrument(app).expose(app, port=8001)

# --- JWT AUTHENTICATION VERIFICATION ---
def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        # Decode the token (Assume 'SECRET_KEY' is your secret key)
        payload = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# --- INGEST DOCUMENT ---
@app.post("/ingest/")
@limiter.limit("5/minute")
async def ingest_document(file: UploadFile = File(...), user: str = Depends(verify_token)) -> Dict[str, str]:
    contents = await file.read()
    text = contents.decode("utf-8")
    document_name = file.filename

    # Split into chunks for RAG
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(text)

    # Insert document record
    conn = await get_db_connection()
    try:
        doc_result = await conn.fetchrow(
            "INSERT INTO documents (name, content) VALUES ($1, $2) RETURNING id",
            document_name, text
        )
        doc_id = doc_result["id"]
    finally:
        await conn.close()

    # Store chunks + embeddings in pgvector
    metadata = [{"document_id": doc_id}] * len(chunks)
    vector_store = get_vector_store()
    vector_store.add_texts(chunks, metadatas=metadata)

    return {
        "message": f"Ingested {len(chunks)} chunks from '{document_name}'",
        "document_id": doc_id
    }

# --- Q&A API ---
@app.post("/query/")
@limiter.limit("5/minute")
async def query_qa(request: Request, user: str = Depends(verify_token)):
    data = await request.json()
    question = data.get("question")
    selected_doc_ids = data.get("document_ids", [])

    retriever = get_vector_store().as_retriever(search_kwargs={"k": 3})
   
    # Filter by selected document IDs if provided
    if selected_doc_ids:
        retriever.search_kwargs["filter"] = {
            "document_id": {"$in": selected_doc_ids}
        }

    llm = Ollama(model="llama3:8b")
    qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
    answer = qa_chain.run(question)

    return {"question": question, "answer": answer}

# --- LIST DOCUMENTS ---
@app.get("/documents/")
async def list_documents(user: str = Depends(verify_token)):
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("SELECT id, name FROM documents")
        return [{"id": row["id"], "name": row["name"]} for row in rows]
    finally:
        await conn.close()

