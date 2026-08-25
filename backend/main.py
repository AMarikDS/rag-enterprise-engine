from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os

from backend.core.config import settings
from backend.core.llm_service import llm_service
from backend.core.qdrant_client import qdrant_db
from backend.core.document_processor import DocumentProcessor

app = FastAPI(title="RAG Backend API")

class ChatRequest(BaseModel):
    query: str
    model: str = "gemini-2.5-flash"
    
class SettingsUpdateRequest(BaseModel):
    docs_dir: str
    chunk_size: int
    chunk_overlap: int

class IndexRequest(BaseModel):
    docs_dir: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None

@app.get("/api/models")
def get_free_models():
    # Provide a list of free models available in Gemini
    return {
        "models": [
            {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash"},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash"},
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro"}
        ]
    }

@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    settings.default_docs_dir = req.docs_dir
    settings.default_chunk_size = req.chunk_size
    settings.default_chunk_overlap = req.chunk_overlap
    return {"status": "ok", "message": "Settings updated temporarily (in-memory)."}

@app.post("/api/index")
def index_documents(req: IndexRequest):
    docs_dir = req.docs_dir or settings.default_docs_dir
    chunk_size = req.chunk_size or settings.default_chunk_size
    chunk_overlap = req.chunk_overlap or settings.default_chunk_overlap
    
    if not os.path.exists(docs_dir):
        raise HTTPException(status_code=400, detail="Directory not found.")
        
    try:
        processor = DocumentProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        texts, metadatas = processor.process_directory(docs_dir)
        
        # We need to batch embeddings generation if there are many texts
        batch_size = 100
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            embeddings = llm_service.generate_embeddings(batch_texts)
            all_embeddings.extend(embeddings)
            
        qdrant_db.add_chunks(texts, all_embeddings, metadatas)
        return {"status": "ok", "message": f"Successfully indexed {len(texts)} chunks."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat(req: ChatRequest):
    try:
        query_vector = llm_service.generate_embeddings([req.query])[0]
        search_results = qdrant_db.search(query_vector=query_vector, limit=3)
        
        context_chunks = [hit.payload.get("text", "") for hit in search_results if hit.payload]
        
        answer = llm_service.generate_answer(query=req.query, context=context_chunks, model=req.model)
        
        return {
            "answer": answer,
            "sources": context_chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
