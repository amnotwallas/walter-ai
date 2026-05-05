# 🧠 WALTER_AI_NEURAL_CORE

Backend engine for Walter Ambriz's interactive portfolio. Built with FastAPI and LLM orchestration.

## 🚀 Key Features

- **LLM Orchestration:** Powered by Groq (Llama 3.1) for high-speed, intelligent interactions.
- **Dynamic Tool Use:** The agent can interact with the portfolio data and trigger UI changes via specialized tools.
- **Centralized Data:** Single source of truth in `data.json` with Pydantic validation.
- **Trace ID Injection:** Every request is tagged with a unique Trace ID for full observability across logs and response headers.
- **Session Persistence:** Optimized memory management that maintains context for the last 6 messages.
- **Hybrid Streaming:** SSE (Server-Sent Events) for fluid, word-by-word responses.
- **Secure Data Serving:** Dedicated endpoints for structured portfolio data and project assets.
- **Advanced Observability:** Structured JSON logging, real-time request tracking, and Trace ID correlation.

## 🛡️ Trust & Safety (Guardrails)

The system integrates multi-layered security directly into the `SYSTEM_PROMPT` to ensure professional behavior:

- **Prompt Protection:** Shielded against injection attacks and instruction extraction attempts.
- **Topic Limitation:** Strictly focused on Walter Ambriz's career, tech stack, and projects.
- **Hallucination Prevention:** Relies exclusively on verified data from `data.json`.

---

## 🛠️ Development Workflow

### Quick Start (cURL)

**Chat Endpoint:**
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
     -H "X-API-KEY: your_key" \
     -H "Content-Type: application/json" \
     -d '{"query": "Tell me about Walter experience", "session_id": "test_123"}'
```

**Secure CV Data:**
```bash
curl -H "X-API-KEY: your_key" http://localhost:8000/api/v1/data
```

### Setup & Commands

Manage the project using the provided `Makefile`:

- **`make install`**: Set up the environment and dependencies.
- **`make dev`**: Run the server with hot-reload for development.
- **`make test`**: Execute the test suite.
- **`make clean`**: Wipe cache and virtual environment.

---

## 🏗️ Technical Architecture

### Tech Stack
- **Framework:** FastAPI
- **LLM Provider:** Groq SDK (Llama 3.1 8B/70B)
- **Validation:** Pydantic v2
- **Logging:** Structured JSON + Console Colors
- **Rate Limiting:** SlowAPI (Fixed Window)

### Modules
- `app/api`: API routes and security.
- `app/services`: Orchestration and intelligence.
- `app/core`: Configuration, logging, and data loading.
- `app/tools`: Executable functions for the AI.
- `app/models`: Data schemas and validation.

---

## 📝 License
Proprietary. Developed by Walter Ambriz.
