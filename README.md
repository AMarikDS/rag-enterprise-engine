<div align="center">
  <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjEyMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiBzdHlsZT0iYmFja2dyb3VuZDogbGluZWFyLWdyYWRpZW50KDkwZGVnLCAjMGYxNzJhLCAjMWUyOTNiKTsgYm9yZGVyLXJhZGl1czogMTJweDsiPgogIDx0ZXh0IHg9IjUwJSIgeT0iNDUlIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSI0MiIgZm9udC13ZWlnaHQ9IjgwMCIgZmlsbD0iIzM4YmRmOCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgbGV0dGVyLXNwYWNpbmc9IjIiPlJBRy1SS1MgRU5HSU5FPC90ZXh0PgogIDx0ZXh0IHg9IjUwJSIgeT0iNzUlIiBmb250LWZhbWlseT0ibW9ub3NwYWNlIiBmb250LXNpemU9IjE2IiBmaWxsPSIjOTRhM2I4IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIj5GYXN0QVBJIOKAoiBSZWZsZXgg4oCiIFFkcmFudCDigKIgR2VtaW5pPC90ZXh0Pgo8L3N2Zz4=" alt="RAG-RKS Engine Banner">
</div>

# RAG System

## Что это за проект и зачем он нужен?

**Retrieval-Augmented Generation (RAG)** — это архитектура, которая наделяет искусственный интеллект "корпоративной памятью". Нейросети (например, ChatGPT или Gemini) обладают обширными, но обобщенными знаниями. Они не знают деталей ваших внутренних регламентов, секретных документов или специфики вашего узкого бизнеса. Если задать им специализированный вопрос, они начнут выдумывать факты (галлюцинировать).

Этот проект решает данную проблему. Он позволяет загрузить ваши собственные конфиденциальные документы (PDF, TXT) и создать закрытую базу знаний. Когда вы задаете вопрос, система:
1. Мгновенно находит в ваших документах самые подходящие абзацы с помощью векторного поиска (Qdrant).
2. Показывает эти абзацы нейросети (Google Gemini).
3. Нейросеть генерирует умный, структурированный и честный ответ, основываясь **исключительно на ваших документах**, и предоставляет ссылки на источники.

Это идеальный инструмент для юристов (анализ договоров), инженеров (поиск по ГОСТам) и корпоративных баз знаний (внутренние регламенты).

---

## Особенности архитектуры

Enterprise-ready система, разработанная для умного семантического поиска. Архитектура строго разделена на высокопроизводительный Backend (FastAPI) и современный UI Frontend (Reflex), с полной оркестрацией через Docker.

## Основные возможности

- **Semantic Vector Search**: Integrated with Qdrant Vector Database for high-speed, meaning-based information retrieval.
- **AI Integration**: Powered by Google Gemini (e.g., 3.7 Flash, 2.5 Pro) for contextual text generation and reasoning.
- **Dynamic Configuration**: Adjustable document parsing chunk sizes and overlapping configurations via UI.
- **Containerized Architecture**: Fully Dockerized environment for seamless deployment and scalability across any infrastructure.
- **Modern Interface**: Professional Glassmorphism UI built with Python (Reflex).

---

## Technology Stack

- **Backend**: FastAPI, Uvicorn, LangChain, Google GenAI, Pydantic, FastEmbed.
- **Frontend**: Reflex (Full-stack Python Web Framework).
- **Database**: Qdrant (Vector Database Engine).
- **Infrastructure**: Docker, Docker Compose.
- **Package Management**: Poetry.

---

## Getting Started

### Prerequisites

Ensure the following dependencies are installed on your host system:
1. Docker Engine
2. Docker Compose

### Environment Configuration

Create a `.env` file in the root directory and specify the required variables:

```ini
GEMINI_API_KEY=your_google_gemini_api_key_here
```

### Deployment

The entire system is orchestrated via Docker Compose. To build and start all services (Frontend, Backend, and Qdrant Database):

```bash
docker-compose up --build -d
```

### Accessing the System

Once the containers are successfully provisioned and running, access the services via:

- **Frontend Application**: [http://localhost:3000](http://localhost:3000)
- **Backend API Documentation**: [http://localhost:8080/docs](http://localhost:8080/docs)

### Stopping the System

To gracefully stop and remove the containers, run:

```bash
docker-compose down
```

---

## Architecture Overview

1. **qdrant**: Runs the official Qdrant rust-based vector database on port `6333`. Data is persisted to the local `./data/qdrant_prod_storage` volume.
2. **backend**: A FastAPI service running on port `8080`. Handles document parsing, vector embedding generation (via MiniLM-L12), Qdrant queries, and LLM communication.
3. **frontend**: A Reflex application running on port `3000` (UI) and `8000` (WebSocket state server). Communicates internally with the backend API.
