from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import json
import uuid

from backend.core.config import settings
from backend.core.llm_service import llm_service
from backend.core.qdrant_client import qdrant_db
from backend.core.document_processor import DocumentProcessor

app = FastAPI(title="RAG Backend API")

indexing_progress = {"status": "idle", "total": 0, "processed": 0, "message": ""}


class ChatRequest(BaseModel):
    query: str
    model: str = "gemini-3.6-flash"
    session_id: str
    kb_name: str


class SettingsUpdateRequest(BaseModel):
    docs_dir: str
    chunk_size: int
    chunk_overlap: int


class IndexRequest(BaseModel):
    kb_name: str
    docs_dir: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None


class HistoryRequest(BaseModel):
    session_id: str
    message: dict


class CreateSessionRequest(BaseModel):
    name: str
    kb_name: str
    model: str = "gemini-3.6-flash"


class UpdateSessionModelRequest(BaseModel):
    model: str


SESSIONS_FILE = os.path.join(os.getcwd(), "data", "sessions.json")


def load_sessions() -> dict:
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_sessions(sessions: dict):
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


def process_indexing_background(
    kb_name: str, docs_dir: str, chunk_size: int, chunk_overlap: int
):
    try:
        indexing_progress["status"] = "processing"
        indexing_progress["message"] = "Чтение файлов..."
        indexing_progress["total"] = 0
        indexing_progress["processed"] = 0

        processor = DocumentProcessor(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        texts, metadatas = processor.process_directory(docs_dir)

        indexing_progress["total"] = len(texts)
        indexing_progress["message"] = "Векторизация..."

        batch_size = 100
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            embeddings = llm_service.generate_embeddings(batch_texts)
            all_embeddings.extend(embeddings)
            indexing_progress["processed"] = min(i + batch_size, len(texts))

        indexing_progress["message"] = "Сохранение в БД..."
        qdrant_db.add_chunks(kb_name, texts, all_embeddings, metadatas)

        indexing_progress["status"] = "done"
        indexing_progress["message"] = f"Готово: {len(texts)} чанков!"
    except Exception as e:
        import traceback

        traceback.print_exc()
        indexing_progress["status"] = "error"
        indexing_progress["message"] = str(e)


@app.get("/api/models")
def get_free_models():
    return {
        "models": [
            {"id": "gemini-3.7-flash", "name": "Gemini 3.7 Flash"},
            {"id": "gemini-3.6-flash", "name": "Gemini 3.6 Flash"},
            {"id": "gemini-3.5-flash", "name": "Gemini 3.5 Flash"},
            {"id": "gemini-flash-latest", "name": "Gemini Flash Latest"},
            {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro"},
        ]
    }


@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    settings.default_docs_dir = req.docs_dir
    settings.default_chunk_size = req.chunk_size
    settings.default_chunk_overlap = req.chunk_overlap
    return {"status": "ok", "message": "Settings updated temporarily (in-memory)."}


@app.get("/api/kb")
def get_knowledge_bases():
    try:
        kbs = qdrant_db.get_collections()
        return {"kbs": kbs}
    except Exception as e:
        return {"kbs": []}


@app.delete("/api/kb/{kb_name}")
def delete_knowledge_base(kb_name: str):
    qdrant_db.delete_collection(kb_name)
    return {"status": "ok"}


@app.get("/api/index/progress")
def get_indexing_progress():
    return indexing_progress


@app.post("/api/index")
def index_documents(req: IndexRequest, background_tasks: BackgroundTasks):
    docs_dir = req.docs_dir or settings.default_docs_dir

    # Smart path resolution for local Mac development
    if docs_dir.startswith("/Users/") and "RAG-RKS" in docs_dir:
        parts = docs_dir.split("RAG-RKS")
        if len(parts) > 1:
            rel_path = parts[1].lstrip("/")
            docs_dir = os.path.join("/app", rel_path)

    chunk_size = req.chunk_size or settings.default_chunk_size
    chunk_overlap = req.chunk_overlap or settings.default_chunk_overlap

    if not os.path.exists(docs_dir):
        raise HTTPException(status_code=400, detail="Directory not found.")

    if indexing_progress["status"] == "processing":
        return {"status": "processing", "message": "Индексация уже идет"}

    background_tasks.add_task(
        process_indexing_background, req.kb_name, docs_dir, chunk_size, chunk_overlap
    )
    return {"status": "started", "message": "Запуск индексации..."}


@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        sessions = load_sessions()
        session_data = sessions.get(req.session_id, {})
        history = session_data.get("messages", [])[
            -6:
        ]  # Последние 6 сообщений для контекста

        query_vector = llm_service.generate_embeddings([req.query])[0]
        search_results = qdrant_db.search(
            collection_name=req.kb_name, query_vector=query_vector, limit=3
        )

        context_chunks = [
            hit.payload.get("text", "") for hit in search_results if hit.payload
        ]

        answer = llm_service.generate_answer(
            query=req.query, context=context_chunks, model=req.model, history=history
        )

        return {"answer": answer, "sources": context_chunks}
    except Exception as e:
        import traceback

        traceback.print_exc()
        err_msg = str(e)
        if (
            "Connection reset by peer" in err_msg
            or "ReadError" in err_msg
            or "ReadTimeout" in err_msg
        ):
            err_msg = "Ошибка соединения с сервером ИИ (возможно, бесплатный лимит запросов исчерпан или сеть нестабильна). Подождите минуту и попробуйте еще раз."
        elif not err_msg.strip():
            err_msg = repr(e)
        raise HTTPException(status_code=500, detail=err_msg)


@app.get("/api/sessions")
def get_sessions():
    sessions = load_sessions()
    # return list without full message history
    result = []
    for sid, sdata in sessions.items():
        result.append(
            {
                "id": sid,
                "name": sdata.get("name", "New Chat"),
                "kb_name": sdata.get("kb_name", ""),
                "model": sdata.get("model", "gemini-3.6-flash"),
            }
        )
    return {"sessions": result}


@app.post("/api/sessions")
def create_session(req: CreateSessionRequest):
    sessions = load_sessions()

    # Check for duplicate names
    for sid, sdata in sessions.items():
        if sdata.get("name") == req.name:
            raise HTTPException(
                status_code=400, detail="Чат с таким именем уже существует"
            )

    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "name": req.name,
        "kb_name": req.kb_name,
        "model": req.model,
        "messages": [],
    }
    save_sessions(sessions)
    return {"session_id": session_id}


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    sessions = load_sessions()
    if session_id in sessions:
        del sessions[session_id]
        save_sessions(sessions)
    return {"status": "ok"}


@app.patch("/api/sessions/{session_id}/model")
def update_session_model(session_id: str, req: UpdateSessionModelRequest):
    sessions = load_sessions()
    if session_id in sessions:
        sessions[session_id]["model"] = req.model
        save_sessions(sessions)
        return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Чат не найден")


@app.get("/api/history")
def get_history(session_id: str):
    sessions = load_sessions()
    sdata = sessions.get(session_id, {})
    return {"history": sdata.get("messages", [])}


@app.post("/api/history")
def append_history(req: HistoryRequest):
    sessions = load_sessions()
    if req.session_id not in sessions:
        sessions[req.session_id] = {"name": "Chat", "kb_name": "", "messages": []}
    sessions[req.session_id]["messages"].append(req.message)
    save_sessions(sessions)
    return {"status": "ok"}
