# fastapi-rag-app
FastAPI + Ollama + PGVector based RAG (Retrieval-Augmented Generation) system with document ingestion and Q&amp;A APIs.

# 📚 FastAPI RAG App

This is a **Retrieval-Augmented Generation (RAG)** application powered by **FastAPI**, **LangChain**, **Ollama (LLaMA 3)**, and **PostgreSQL with pgvector**. It enables document ingestion, vector embedding, and natural language Q&A over your content.

---

## 🚀 Features

- 🔹 Upload `.txt` documents
- 🔹 Generate text embeddings using Ollama's LLaMA 3
- 🔹 Store embeddings in PostgreSQL with pgvector
- 🔹 Ask questions and get answers from ingested documents using LangChain's RetrievalQA
- 🔹 RESTful API with Swagger UI at `/docs`

---

## 🧠 Tech Stack

- **FastAPI** — for building the API
- **LangChain** — text splitter, embedding, and retrieval pipeline
- **Ollama** — local LLMs like LLaMA 3 for Q&A
- **PGVector + PostgreSQL** — vector store for similarity search
- **asyncpg** — async DB connection

---

## 🛠️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/fastapi-rag-app.git
cd fastapi-rag-app

