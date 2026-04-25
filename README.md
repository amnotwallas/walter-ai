# 🤖 WALTER_AI_API // Neural Core

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat&logo=vercel&logoColor=white)](https://vercel.com/)
[![LLM](https://img.shields.io/badge/LLM-Groq_Llama3.1-orange?style=flat)](https://groq.com/)

**WALTER_AI_API** is an advanced Multi-Agent system powering the interactive intelligence of Walter Ambriz's portfolio. More than just a chat, this API implements a **Master Orchestrator** capable of executing specialized tools to retrieve precise data from Walter's professional modules.

## 🚀 Advanced Features

- **Multi-Agent Orchestration:** Uses a **Router-Worker** pattern where a Master Agent delegates tasks to specialized data agents.
- **Tool-Use (Function Calling):** The LLM dynamically decides which internal functions (`get_projects`, `get_experience`, `get_personal_info`) to execute based on user intent.
- **Hybrid SSE Streaming:** Delivers real-time word-by-word responses while simultaneously streaming technical "Core Logs" during tool execution.
- **Context-Aware Memory:** Maintains short-term conversational history for seamless multi-turn interactions.
- **Clean Architecture:** Enterprise-grade separation of concerns (Providers, Services, Tools, Schemas).

## 🏗️ Technical Architecture

```text
api/
├── app/
│   ├── api/v1/         # Route versioning and endpoints
│   ├── core/           # Config, Prompts, and Security
│   ├── models/         # Pydantic data validation
│   ├── services/       # Master Agent & Business Logic
│   ├── providers/      # LLM Gateway (Groq/Llama 3.1)
│   └── tools/          # Specialized Data Agents (Tool Definitions)
├── main.py             # App entry point
└── Makefile            # Standardized workflow
```

---

## 🛠️ Development Workflow

### Prerequisites
- **Python 3.11+**
- **Groq API Key:** Get it at [Groq Cloud](https://console.groq.com/).

### Setup
1. Create a `.env` file:
   ```env
   GROQ_API_KEY=your_key_here
   API_KEY=your_secure_shield_token
   ```
2. Standard commands:
   - `make install`: Build virtual environment.
   - `make dev`: Launch FastAPI with hot-reload.
   - `make test`: Execute Pytest suite.

---

## 🔌 Intelligence Endpoints

- `GET /health`: Metadata and system status.
- `POST /api/v1/chat`: Synchronous multi-agent response.
- `POST /api/v1/chat/stream`: **Real-time SSE stream** featuring Tool-Execution logs.

## 🛡️ Security Engine

- **Shielded API:** Validates `X-API-KEY` headers for all intelligence requests.
- **CORS Lock:** Restricted to authorized portfolio origins only.
- **Data Integrity:** Pydantic strictly enforces schema validation.

---
*Architected for high-performance AI integration // Walter Ambriz*
