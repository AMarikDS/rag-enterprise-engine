<div align="center">
  <code>UkFHLVJLUzogUmV0cmlldmFsLUF1Z21lbnRlZCBHZW5lcmF0aW9uIFN5c3RlbSAoRmFzdEFQSSArIFJlZmxleCArIFFkcmFudCArIEdlbWluaSk=</code>
  <br/>
  <i>Retrieval-Augmented Generation System</i>
</div>

# RAG System

Enterprise-ready Retrieval-Augmented Generation (RAG) system designed for intelligent document search and semantic interactions. The architecture is strictly decoupled into a high-performance Backend (FastAPI) and a modern UI Frontend (Reflex), orchestrated entirely via Docker.

## Core Features

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
