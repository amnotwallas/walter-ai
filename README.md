# WALTER-AI

> **Motor de orquestación multiagente asíncrono** diseñado para actuar como una interfaz inteligente entre usuarios y un repositorio de datos profesionales estructurados. Implementa una arquitectura hexagonal limpia basada en el patrón **ReAct (Reasoning and Acting)** con FastAPI, LiteLLM y proveedores de LLM como Groq.

---

## Stack Tecnológico Principal

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Pydantic-v2-E92063?style=flat-square&logo=pydantic&logoColor=white" alt="Pydantic" />
  <img src="https://img.shields.io/badge/LiteLLM-Integrated-blue?style=flat-square" alt="LiteLLM" />
  <img src="https://img.shields.io/badge/Package_Manager-uv-blue?style=flat-square" alt="UV" />
  <img src="https://img.shields.io/badge/Deploy-Vercel-000000?style=flat-square&logo=vercel&logoColor=white" alt="Vercel" />
</p>

---

## Tabla de Contenidos

- [1. Introducción Técnica](#1-introducción-técnica)
- [2. Arquitectura del Sistema](#2-arquitectura-del-sistema)
- [3. Estructura del Proyecto](#3-estructura-del-proyecto)
- [4. Especificación de Agentes](#4-especificación-de-agentes)
- [5. Diagrama de Interacción](#5-diagrama-de-interacción)
- [6. Capa de Seguridad y Guardrails](#6-capa-de-seguridad-y-guardrails)
- [7. Documentación de Endpoints](#7-documentación-de-endpoints)
- [8. Configuración y Despliegue](#8-configuración-y-despliegue)
- [9. Licencia](#9-licencia)

---

## 1. Introducción Técnica

WALTER-AI es un backend de alto rendimiento desarrollado con **FastAPI**. Su propósito principal es la resolución de consultas complejas mediante la descomposición funcional de tareas, permitiendo que un orquestador central coordine agentes especializados en la recuperación de información y ejecución de acciones en tiempo real (por ejemplo, navegaciones automáticas en la UI del portafolio).

> [!NOTE]
> Toda la lógica corre bajo un flujo asíncrono optimizado mediante el gestor de paquetes de alto rendimiento `uv`.

---

## 2. Arquitectura del Sistema

El flujo de ejecución separa los controladores (HTTP/SSE), la capa de negocio (servicios y modelos de dominio) y los adaptadores de infraestructura para APIs externas o persistencia, siguiendo los principios de la arquitectura hexagonal:

```mermaid
graph TD
    %% Nodos Principales
    A[Client / UI]
    B[FastAPI Router]
    C{Security & Limiter}
    D[AgentService Orchestrator]
    E[403 Forbidden]
    F[Memory Provider]
    G["Context Provider <br/> (data.json)"]
    H["LLM: LiteLLM <br/> (Groq / OpenAI / Anthropic)"]
    I[Tool Registry]

    %% Conexiones de Entrada
    A -->|POST /chat & /chat/stream| B
    B --> C
    C -->|Valid API Key| D
    C -->|Invalid| E

    D --> F
    D --> G

    %% Bucle ReAct y Sub-Herramientas
    D <-->|Tools Schemas| H
    D -->|Call| I

    subgraph Functional_Tools ["Herramientas de Agentes (CV Tools)"]
        T1[Biographical Agent]
        T2[Project Agent]
        T3[Experience Agent]
        T4[Navigation Agent]
        T5[UI Agent]
    end

    I --> T1
    I --> T2
    I --> T3
    I --> T4
    I --> T5

    T1 -->|Result| D
    T2 -->|Result| D
    T3 -->|Result| D
    T4 -->|Result| D
    T5 -->|Result| D

    D -->|SSE Stream / JSON| A

    %% Componente de Registro (Logger)
    subgraph Logging_System ["Sistema de Logs (Structured JSON)"]
        L[ServerLogger]
        
        %% Métricas/Campos Guardados
        M1["HTTP Metadata <br/> (method, path, status, latency_ms, IP)"]
        M2["LLM Tokens <br/> (input_tokens, output_tokens, total_tokens)"]
        M3["Execution Logs <br/> (tool_name, arguments, success/error)"]
        M4["Metadata & Context <br/> (timestamp, level, trace_id, module)"]
    end

    %% Conexiones de Logging
    B -.->|Genera & Propaga| M4
    B -.->|Registra| M1
    H -.->|Reporta Consumo| M2
    
    T1 -.->|Registra Ejecución| M3
    T2 -.->|Registra Ejecución| M3
    T3 -.->|Registra Ejecución| M3
    T4 -.->|Registra Ejecución| M3
    T5 -.->|Registra Ejecución| M3

    M1 --> L
    M2 --> L
    M3 --> L
    M4 --> L

    L -->|Escribe| Out[(server.log / stdout)]

    %% Definición de Estilos (Premium UI UX)
    classDef client fill:#dbeafe,stroke:#1e40af,stroke-width:2px,color:#1e3a8a;
    classDef router fill:#f3e8ff,stroke:#6b21a8,stroke-width:2px,color:#581c87;
    classDef security fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f;
    classDef orchestrator fill:#ede9fe,stroke:#4c1d95,stroke-width:2px,color:#2e1065;
    classDef error fill:#fee2e2,stroke:#b91c1c,stroke-width:2px,color:#7f1d1d;
    classDef provider fill:#f3f4f6,stroke:#374151,stroke-width:2px,color:#111827;
    classDef execution fill:#e0f2fe,stroke:#0369a1,stroke-width:2px,color:#0c4a6e;
    classDef tools fill:#ecfdf5,stroke:#059669,stroke-width:2px,color:#065f46;
    classDef logger fill:#1f2937,stroke:#3b82f6,stroke-width:2px,color:#f3f4f6;
    classDef metrics fill:#fff7ed,stroke:#ea580c,stroke-width:1px,color:#7c2d12;

    class A client;
    class B router;
    class C security;
    class D orchestrator;
    class E error;
    class F,G provider;
    class H,I execution;
    class T1,T2,T3,T4,T5 tools;
    class L,Out logger;
    class M1,M2,M3,M4 metrics;
```

---

## 3. Estructura del Proyecto

```text
walter-ai/
├── app/
│   ├── adapters/       # Adaptadores externos (controladores, datos, LLM)
│   │   ├── controllers/# Endpoints y definición de rutas FastAPI (v1)
│   │   ├── data/       # Cargador de datos (JSONDataLoaderAdapter)
│   │   └── llm/        # Implementación del cliente LLM usando LiteLLM
│   ├── config/         # Configuración basada en YAML (config.yml)
│   ├── core/           # Configuración, logs globales, dependencias y seguridad
│   ├── data/           # Repositorio de datos estructurados (data.json)
│   ├── domain/         # Capa de dominio (lógica de negocio pura)
│   │   ├── models/     # Esquemas de Pydantic y modelos de dominio
│   │   ├── ports/      # Puertos de entrada/salida (interfaces)
│   │   └── services/   # Lógica central del orquestador (AgentService)
│   ├── templates/      # Plantillas HTML de prueba (chat_ui.html)
│   └── tools/          # Registro y definición de herramientas (CV Tools)
├── tests/              # Suite de pruebas unitarias y de integración
├── main.py             # Punto de entrada principal de la aplicación FastAPI
├── Makefile            # Tareas de automatización comunes
└── pyproject.toml      # Configuración de dependencias y herramientas
```

---

## 4. Especificación de Agentes

El sistema mapea agentes especializados como herramientas (tools) registradas en el orquestador:

| Agente                 | Rol Específico                                       | Modelo (LLM) | Herramientas Asociadas                                        |
| :--------------------- | :--------------------------------------------------- | :----------- | :------------------------------------------------------------ |
| **Biographical Agent** | Datos biográficos, académicos y de contacto.         | Dinámico     | `get_personal_info`                                           |
| **Project Agent**      | Consulta técnica y búsqueda en el portafolio.        | Dinámico     | `get_projects_list`, `get_project_by_slug`, `search_projects` |
| **Experience Agent**   | Recuperación y análisis de historial laboral.        | Dinámico     | `get_experience_info`                                         |
| **Navigation Agent**   | Control de redirección de la interfaz gráfica.       | Dinámico     | `trigger_navigation`                                          |
| **UI Agent**           | Manipulación de elementos visuales (foco/highlight). | Dinámico     | `highlight_element`                                           |

> [!NOTE]
> El LLM es resuelto dinámicamente según la configuración de `app/config/config.yml`. Por defecto utiliza `groq/meta-llama/llama-4-scout-17b-16e-instruct` mediante LiteLLM, pero es compatible con cualquier proveedor soportado por LiteLLM (OpenAI, Anthropic, Groq, etc.).

---

## 5. Diagrama de Interacción

El ciclo ReAct asíncrono interactúa de la siguiente manera:

```mermaid
sequenceDiagram
    participant U as Usuario
    participant O as Orquestador (AgentService)
    participant L as LLM (LiteLLM Adapter)
    participant A as Agentes Funcionales (Tools)

    U->>O: Consulta (ej: "Muestra detalles del proyecto X")
    O->>O: Cargar Memoria y Contexto
    O->>L: Query + Contexto + Definición de Tools
    L->>O: Tool Call: get_project_by_slug(slug="X")
    O->>A: Ejecutar Project Agent
    A->>O: Datos estructurados del proyecto
    O->>L: Resultado de Tool + Query Original
    L->>O: Generar Respuesta Final + Tool Call: trigger_navigation
    O->>A: Ejecutar Navigation Agent
    O->>U: Stream SSE (Respuesta texto + Acción UI)
```

---

## 6. Capa de Seguridad y Guardrails

Antes de realizar llamadas a los LLMs, el motor valida de forma estricta las entradas para mitigar abusos:

- **Filtro contra Inyecciones (Prompt Injection):** Expresiones regulares acotadas por límites de palabra (`\b`) bloquean patrones de desborde de reglas (_"forget rules"_, _"act as..."_) sin generar falsos positivos en palabras clave válidas como _"contactar"_.
- **Restricción de Longitud:** Limita la consulta a **300 caracteres** para prevenir desbordamiento de contexto deliberado.
- **Limpieza de Formato:** Intercepta el uso excesivo de caracteres especiales (`{}`, `[]`, `<>`) para bloquear inyecciones de plantillas.
- **Saneamiento de Parámetros:** Normaliza de forma transparente los argumentos nulos del LLM (ej. `"null"` en JSON) convirtiéndolos a `{}` antes de invocar las herramientas de Python.

---

## 7. Documentación de Endpoints

El sistema expone una API RESTful autodocumentada bajo el estándar OpenAPI.

### Chat y Streaming

- **`POST /api/v1/chat`**
  - **Propósito:** Devuelve la respuesta completa de la consulta en formato JSON.
  - **Encabezados Requeridos:** `X-API-KEY` (para autenticación y Rate Limit).

- **`POST /api/v1/chat/stream`**
  - **Propósito:** Stream de respuestas utilizando SSE (Server-Sent Events).
  - **Encabezados Requeridos:** `X-API-KEY` (para autenticación y Rate Limit).

> [!IMPORTANT]
> Todas las peticiones a los endpoints de chat requieren el encabezado `X-API-KEY` para validar la identidad del cliente y aplicar políticas de Rate Limiting.

<details>
<summary><b>Ver estructura del payload (Request Body)</b></summary>

```json
{
  "query": "Como puedo contactar a Walter?",
  "session_id": "973884a3-3c5e-4004-86fb-21057f198a35",
  "action": "chat",
  "history": [],
  "context": {
    "url": "http://localhost:4200/home",
    "page": "home",
    "project_slug": null
  }
}
```

</details>

<details>
<summary><b>Ver ejemplo de respuesta de Stream (SSE Chunks)</b></summary>

```text
data: {"message": "Puedes contactar a ", "actions": []}

data: {"message": "Walter a través de su correo...", "actions": []}
```

</details>

### Datos del Portafolio y Activos

- **`GET /api/v1/data`**
  - **Propósito:** Obtener la información estructurada de todo el portafolio (equivalente a `data.json`).
  - **Encabezados Requeridos:** `X-API-KEY`.

- **`GET /api/v1/assets/{project_name}/{image_name}`**
  - **Propósito:** Distribución protegida de imágenes y assets de los proyectos.
  - **Encabezados Requeridos:** `X-API-KEY`.

---

## 8. Configuración y Despliegue

### Requisitos Previos e Instalación

El proyecto utiliza `uv` para garantizar la reproducibilidad y rapidez del entorno virtual:

```bash
# Sincronizar e instalar dependencias
make install
```

### Ejecución de Pruebas

Valida la suite de pruebas unitarias y de integración del backend. Debido a las rutas de los módulos en la arquitectura, es necesario definir la ruta de Python actual:

```bash
# Ejecutar suite de pruebas con la ruta de Python establecida
PYTHONPATH=. make test

# Ejecución manual alternativa:
PYTHONPATH=. uv run pytest tests/
```

### Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto basándote en `.env.example`:

```env
API_KEY=tu_token_secreto_para_la_api
GROQ_API_KEY=tu_groq_api_key
OPENAI_API_KEY=tu_openai_api_key_opcional
ANTHROPIC_API_KEY=tu_anthropic_api_key_opcional
```

### Configuración del LLM (LiteLLM)

El archivo `app/config/config.yml` controla la configuración del modelo de lenguaje y la temperatura de inferencia:

```yaml
llm:
  model: groq/meta-llama/llama-4-scout-17b-16e-instruct
  temperature: 0.5
```

> [!TIP]
> Si deseas desplegar en **Vercel**, asegúrate de sincronizar primero el archivo de requerimientos estándar:
>
> ```bash
> make export
> ```

---

## 9. Licencia

Software propietario desarrollado por **Walter Ambriz**. Todos los derechos reservados.
