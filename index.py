from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import groq
from dotenv import load_dotenv

# Cargar variables de entorno si estamos en local
load_dotenv()

app = FastAPI()

# Configuración de CORS para permitir peticiones desde GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción puedes cambiar esto por tu dominio de GitHub Pages
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar cliente de Groq
client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"))

CV_DATA = {
    "basics": {
        "name": "Walter Jahir Ambriz Reyna",
        "label": "Backend & AI Engineer",
        "summary": "Backend & AI Engineer with production experience building systems that connect LLMs, APIs, and live data sources into reliable, scalable services using Python and FastAPI. Specialized in multi-agent orchestration, LLM integration, and automated evaluation pipelines.",
        "skills": ["Python", "FastAPI", "LLM Integration", "Agent Orchestration", "MLflow", "Docker", "SQL Server"]
    },
    "work": [
        {
            "company": "IBICARE",
            "position": "Backend & AI Engineer",
            "summary": "Built production backend services using Python and FastAPI, connecting LLM agents with live biometric data."
        }
    ],
    "projects": [
        {"name": "AI-Powered Interactive Portfolio", "tech": "Angular, Vercel, LLM"},
        {"name": "Multi-Agent Orchestration System", "tech": "Python, FastAPI, OpenAI, LangChain"}
    ]
}

SYSTEM_PROMPT = f"""
Eres WALTER_AI, el asistente virtual avanzado de Walter Ambriz. 
Tu personalidad es profesional, técnica, eficiente y con un ligero toque de terminal 'cyber-retro'.

REGLAS CRÍTICAS:
1. Responde de forma concisa (máximo 2-3 líneas).
2. Usa mayúsculas ocasionalmente para términos técnicos para mantener la estética de terminal.
3. Si no tienes un dato específico en el CV, di: [DATA_NOT_FOUND].

REGLAS DE NAVEGACIÓN (IMPORTANTE):
- Si el usuario quiere ver tu CV, experiencia o perfil, incluye el tag [NAV:CV] al final.
- Si el usuario pregunta por tus proyectos o trabajos realizados, incluye el tag [NAV:PROJECTS] al final.

CONTEXTO DE WALTER AMBRIZ:
{CV_DATA}
"""

class ChatRequest(BaseModel):
    query: str

@app.get("/api")
async def root():
    return {"status": "WALTER_AI_CORE_ONLINE", "version": "1.0.4"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not os.environ.get("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY_NOT_CONFIGURED")

    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": request.query}
            ],
            temperature=0.5,
            max_tokens=150
        )
        
        response_text = completion.choices[0].message.content
        return {"response": response_text}
        
    except Exception as e:
        print(f"Error: {e}")
        return {"response": "SYSTEM_ERROR: UNABLE_TO_REACH_NEURAL_CORE."}
