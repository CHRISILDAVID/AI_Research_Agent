# 🧠 AI Research Agent

An **agentic AI system** that autonomously researches any topic by orchestrating multi-agent tool-calling pipelines via **LangGraph**. Features a **RAG knowledge base** (ChromaDB), **web search** (Tavily), **FastAPI** backend, and a premium **React** frontend — all containerized with **Docker** and shipped via **GitHub Actions CI/CD**.

> **Architecture**: Supervisor → Researcher → Writer multi-agent loop with autonomous tool-calling

### 🔴 Live Demo
- **Frontend (Vercel)**: [https://ai-research-agent-lime.vercel.app](https://ai-research-agent-lime.vercel.app)
- **Backend (Render)**: [https://ai-research-agent-backend-7z8c.onrender.com](https://ai-research-agent-backend-7z8c.onrender.com)

---

## ✨ Features

- 🤖 **Multi-Agent Orchestration** — Supervisor, Researcher, and Writer agents collaborate autonomously via LangGraph `StateGraph`
- 🔧 **Autonomous Tool-Calling** — Agents decide which tools to invoke (web search, RAG query, document loader, report generator)
- 🔍 **Real-Time Web Search** — Tavily API integration for AI-optimized search results
- 📚 **Dynamic RAG Pipeline** — ChromaDB vector store builds an on-the-fly knowledge base per research session
- 📄 **PDF Document Upload** — Upload research papers and documents for agent-indexed analysis
- ⚡ **Real-Time Streaming** — WebSocket connection streams agent status, tool calls, and progress to the UI
- 📝 **Structured Reports** — Auto-generated Markdown reports with citations and source attribution
- 🐳 **Docker Containerized** — Full-stack deployment with `docker-compose`
- 🔄 **CI/CD Pipeline** — GitHub Actions: Lint → Test → Build → Deploy
- ☁️ **Cloud-Ready** — Pre-configured for GCP Cloud Run deployment

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                  │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  Chat UI  │  │ Agent Status │  │   Research Report View   │  │
│  └─────┬────┘  └──────┬───────┘  └──────────┬───────────────┘  │
│        │               │                     │                  │
│        └───────────────┼─────────────────────┘                  │
│                        │ WebSocket + REST                       │
└────────────────────────┼────────────────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────────────────┐
│                  Backend (FastAPI)                              │
│  ┌─────────────┐  ┌───┴───────────┐  ┌──────────────────────┐   │
│  │  REST API   │  │   WebSocket   │  │   File Upload API    │   │
│  └──────┬──────┘  └───────┬───────┘  └──────────┬───────────┘   │
│         └─────────────────┼──────────────────────┘              │
│                           │                                     │
│  ┌────────────────────────┼──────────────────────────────────┐  │
│  │              LangGraph Agent Pipeline                     │  │
│  │                                                           │  │
│  │  ┌────────────┐    ┌────────────┐    ┌────────────┐       │  │
│  │  │ Supervisor │───▶│ Researcher │───▶│   Writer   │      │  │
│  │  │   Agent    │◀───│   Agent    │◀───│   Agent    │      │  │
│  │  └────────────┘    └─────┬──────┘    └─────┬──────┘       │  │
│  │                          │                 │              │  │
│  │                    ┌─────┴──────┐    ┌─────┴──────┐       │  │
│  │                    │   Tools    │    │   Tools    │       │  │
│  │                    │ • Web Search│    │ • RAG Query│      │  │
│  │                    │ • Doc Load │    │ • Report   │       │  │
│  │                    │ • RAG Query│    │   Generator│       │  │
│  │                    └─────┬──────┘    └────────────┘       │  │
│  │                          │                                │  │
│  └──────────────────────────┼────────────────────────────────┘  │
│                             │                                   │
│  ┌──────────────────────────┼────────────────────────────────┐  │
│  │          ChromaDB Vector Store (per-session)              │  │
│  │     Semantic Embeddings (Gemini) • Similarity Search      │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Agent Framework** | LangGraph (StateGraph, conditional routing, tool-calling) |
| **LLM** | Google Gemini (gemini-2.5-flash) |
| **RAG / Vector DB** | ChromaDB + Gemini Embeddings |
| **Web Search** | Tavily API (AI-optimized search) |
| **Backend** | Python 3.11, FastAPI, WebSocket |
| **Frontend** | React 19, Vite, react-markdown, Lucide Icons |
| **Containerization** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions (Lint → Test → Build → Deploy) |
| **Cloud** | GCP Cloud Run (deployment-ready) |
| **Linting** | Ruff (Python), ESLint (JavaScript) |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- API Keys: [Google AI Studio](https://aistudio.google.com/) + [Tavily](https://tavily.com)

### 1. Clone & Configure

```bash
git clone https://github.com/CHRISILDAVID/AI_Research_Agent.git
cd AI_Research_Agent

# Configure environment
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY and TAVILY_API_KEY
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python -m app.main
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Open Browser
Navigate to [http://localhost:5173](http://localhost:5173)

---

## 🐳 Docker (Full Stack)

```bash
# Copy and configure .env
cp .env.example .env

# Build and run everything
docker-compose up --build

# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/research` | Start a new research session |
| `GET` | `/api/research/{id}` | Get session results |
| `GET` | `/api/sessions` | List all sessions |
| `DELETE` | `/api/research/{id}` | Delete a session |
| `POST` | `/api/upload` | Upload a PDF/text document |
| `GET` | `/api/health` | Health check |
| `WS` | `/ws/research/{id}` | Real-time research streaming |

---

## 🔄 CI/CD Pipeline

The GitHub Actions workflow runs on every push to `main`:

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────┐
│  Lint   │───▶│  Test   │───▶│  Build  │───▶│  Deploy     │
│ Ruff    │    │ pytest  │    │ Docker  │    │ Cloud Run   │
│ ESLint  │    │         │    │ Images  │    │ (optional)  │
└─────────┘    └─────────┘    └─────────┘    └─────────────┘
```

---

## 📂 Project Structure

```
AI_Research_Agent/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Environment configuration
│   │   ├── agents/
│   │   │   ├── graph.py         # LangGraph StateGraph orchestration
│   │   │   ├── supervisor.py    # Supervisor agent (routing decisions)
│   │   │   ├── researcher.py    # Research agent (tool-calling)
│   │   │   ├── writer.py        # Writer agent (report synthesis)
│   │   │   └── state.py         # Shared agent state schema
│   │   ├── tools/
│   │   │   ├── web_search.py    # Tavily web search tool
│   │   │   ├── document_loader.py  # PDF/text document loader
│   │   │   ├── rag_query.py     # RAG semantic search tool
│   │   │   └── report_gen.py    # Report generation tool
│   │   ├── rag/
│   │   │   ├── vectorstore.py   # ChromaDB management
│   │   │   ├── embeddings.py    # Gemini embedding provider
│   │   │   └── chunker.py       # Text chunking utilities
│   │   ├── api/
│   │   │   ├── routes.py        # REST endpoints
│   │   │   └── websocket.py     # WebSocket streaming
│   │   └── models/
│   │       └── schemas.py       # Pydantic data models
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main application
│   │   ├── components/
│   │   │   ├── AgentStatus.jsx  # Real-time agent pipeline display
│   │   │   ├── ResearchReport.jsx  # Markdown report renderer
│   │   │   └── FileUpload.jsx   # PDF drag-and-drop upload
│   │   └── hooks/
│   │       ├── useWebSocket.js  # WebSocket connection manager
│   │       └── useResearch.js   # REST API interactions
│   ├── vite.config.js
│   └── Dockerfile
├── docker-compose.yml
├── .github/workflows/ci-cd.yml
├── .env.example
└── README.md
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 📜 License

This project is licensed under the MIT License.
