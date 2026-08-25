from fastapi import FastAPI, HTTPException, BackgroundTasks

# ...

app = FastAPI(title="RAG Backend API")

indexing_progress = {
    "status": "idle",
    "total": 0,
    "processed": 0,
    "message": ""
}

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

class HistoryRequest(BaseModel):
    docs_dir: str
    message: dict

HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def process_indexing_background(docs_dir: str, chunk_size: int, chunk_overlap: int):
    global indexing_progress
    try:
        indexing_progress["status"] = "processing"
        indexing_progress["message"] = "Чтение файлов..."
        indexing_progress["total"] = 0
        indexing_progress["processed"] = 0
        
        processor = DocumentProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        texts, metadatas = processor.process_directory(docs_dir)
        
        indexing_progress["total"] = len(texts)
        indexing_progress["message"] = "Векторизация..."
        
        batch_size = 100
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            embeddings = llm_service.generate_embeddings(batch_texts)
            all_embeddings.extend(embeddings)
            indexing_progress["processed"] = min(i + batch_size, len(texts))
            
        indexing_progress["message"] = "Сохранение в БД..."
        qdrant_db.add_chunks(texts, all_embeddings, metadatas)
        
        indexing_progress["status"] = "done"
        indexing_progress["message"] = f"Готово: {len(texts)} чанков!"
    except Exception as e:
        indexing_progress["status"] = "error"
        indexing_progress["message"] = str(e)

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

@app.get("/api/index/progress")
def get_indexing_progress():
    return indexing_progress

@app.post("/api/index")
def index_documents(req: IndexRequest, background_tasks: BackgroundTasks):
    docs_dir = req.docs_dir or settings.default_docs_dir
    chunk_size = req.chunk_size or settings.default_chunk_size
    chunk_overlap = req.chunk_overlap or settings.default_chunk_overlap
    
    if not os.path.exists(docs_dir):
        raise HTTPException(status_code=400, detail="Directory not found.")
        
    if indexing_progress["status"] == "processing":
        return {"status": "processing", "message": "Индексация уже идет"}
        
    background_tasks.add_task(process_indexing_background, docs_dir, chunk_size, chunk_overlap)
    return {"status": "started", "message": "Запуск индексации..."}

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

@app.get("/api/history")
def get_history(docs_dir: str):
    history = load_history()
    return {"history": history.get(docs_dir, [])}

@app.post("/api/history")
def append_history(req: HistoryRequest):
    history = load_history()
    if req.docs_dir not in history:
        history[req.docs_dir] = []
    history[req.docs_dir].append(req.message)
    save_history(history)
    return {"status": "ok"}
