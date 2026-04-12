# 🛡️ Risk Auditor Agent (AIXel Case Assignment)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](#)
[![LangGraph](https://img.shields.io/badge/LangGraph-1C3C5A?style=for-the-badge)](#)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](#)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6B6B?style=for-the-badge)](#)

An enterprise-grade, Multi-Agent Risk Management Assistant designed to parse, query, and enforce compliance parameters (e.g., OSFI Guideline E-23) utilizing a decoupled microservice architecture.

## 🌟 Core Technologies & Features

1. **Stateful Agentic Graph (LangGraph)**
   The core reasoning engine operates as a finite state machine rather than a linear chain. It utilizes a `PostgresSaver` checkpointer tied to user session IDs (`thread_id`), allowing true persistent conversational memory across server restarts.

2. **Contextual RAG & Query Expansion**
   Overcomes traditional dumb-retrieval limitations. A secondary LLM node evaluates chat history, resolves pronouns (e.g. "what does _it_ mean?"), and rewrites queries into explicitly detailed search terms before hitting the vector database.

3. **Self-Correction Hallucination Loop (Logic Auditor)**
   Features a strict, dedicated "Judge Node". Before presenting any risk-control answer to the user, the Logic Auditor evaluates the LLM's response against the raw ChromaDB context. If it detects unverified hallucinations, it generates a scathing feedback rejection and forces the retrieving agent to correct itself (with a hard circuit-breaker to prevent infinite loops).

4. **Decoupled Microservice Architecture**
   Vector embeddings run locally via `HuggingFaceEmbeddings(all-MiniLM-L6-v2)` piped directly into a standalone `ChromaDB` Docker container. Application state is handled by a separate `Postgresql` instance.

5. **Premium Cyberpunk Glassmorphism UI**
   A dual-pane web application built on Vite + React + TailwindCSS v4 with drag-and-drop document upload and fluid micro-animations.

## 🚀 Quick Start

### 1. Start Infrastructure (Databases)
```bash
# Spins up Postgres (state management) and ChromaDB (vector store)
docker compose up -d
```

### 2. Start Frontend UI
```bash
cd frontend
npm install
npm run dev
```

### 3. Start Backend AI Engine
```bash
# Requires an environment variable for LLM invocation
export OPENROUTER_API_KEY="your-api-key"

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python backend/app/main.py
```
Visit `http://localhost:5173` to interact with the auditor interface!

## 🏢 AIXel FAQ (Architecture Decisions)

### 1. What are the key features in the system?
Unlike basic RAG scripts, this is a multi-agent system boasting **Conversational History Contextualization**, an independent **Hallucination Evaluation Checkpoint**, and an **Interactive Web UI** to upload arbitrary PDF guidelines dynamically.

### 2. What are the major components in the system?
- **Frontend Layer**: React + TailwindCSS providing a split-pane dynamic view.
- **Microservices Backbone**: Dockerized Postgres and ChromaDB ensuring the AI backend runs entirely statelessly.
- **API Engine**: FastAPI asynchronously routing requests to LangGraph pipelines.
- **RAG & Vector Storage**: Langchain text splitting leveraging HuggingFace embeddings.
- **Reasoning Graph**: LangGraph managing flow control (Dispatcher -> Retriever -> Generator -> Auditor).

### 3. Why did you choose this specific way to handle memory?
Memory is managed by **LangGraph PostgresSaver**. Traditional Langchain arrays require massive explicit token injection manually. The Checkpointer ties history natively to an established Postgres connection pool based on session `thread_id`s. This supports enterprise horizontal scaling: if you spin up 5 instances of the FastAPI server behind a load balancer, memory requests continue to work flawlessly.

### 4. How did you ensure the system is fast?
- **Local Embeddings**: `HuggingFaceEmbeddings` runs on the local CPU avoiding external network latency for simple text-vector parsing.
- **Async Threading**: FastAPI is non-blocking. Database pools (psycopg) run entirely on Python's async event loop.

### 5. How did you ensure the system is stable?
- **Strict Pipeline Failsafes**: The LangGraph structure possesses an isolated `auditor_node`. If the generation LLM hallucinates outside the exact retrieved bounds, the auditor node flags it, prevents transmission to the user, and forces a re-retrieval loop utilizing the penalizing feedback.
- **Circuit Breakers**: Re-retrieval loops are hard-capped at 3 maximum attempts to prevent infinite LLM ping-pong deadlocks. 

### 6. What would you do differently if you had a month instead of three days?
*Note: I have already proactively over-delivered on portions of the initial one-month vision (e.g. Postgres persistent state, dockerized microservices, Logic Auditor self-reflection loop).*
If given a full month, I would integrate:
1. **Semantic Node Chunking**: Replacing `RecursiveCharacterTextSplitter` with NLP-based semantic parsers to ensure that risk protocols are never severed mid-sentence or mid-logic block.
2. **Human-In-The-Loop (HITL) Authorizations**: Utilizing LangGraph's `interrupt_before` capability to freeze pipeline workflows and prompt the web UI for physical human click-approvals before publishing definitive risk assessments.
3. **Multi-Vector Retrieval**: Extracting and intelligently querying the actual nested tables and visual graphs commonly found in PDF compliance standards.
