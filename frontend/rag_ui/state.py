import reflex as rx
import httpx
import os
from pydantic import BaseModel
from typing import List

API_URL = "http://localhost:8080/api"

class ChatMessage(BaseModel):
    text: str
    is_user: bool
    sources: List[str] = []

class State(rx.State):
    # Chat State
    chat_history: list[ChatMessage] = []
    current_query: str = ""
    is_loading: bool = False
    
    # Settings State
    docs_dir: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs")
    chunk_size: int = 1000
    chunk_overlap: int = 200
    selected_model: str = "gemini-1.5-flash"
    available_models: list[str] = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.5-flash"]
    
    indexing_progress_val: int = 0
    indexing_status: str = ""
    is_indexing: bool = False

    async def start_indexing(self):
        self.is_indexing = True
        self.indexing_progress_val = 0
        self.indexing_status = "Запуск индексации..."
        yield
        
        try:
            import asyncio
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_URL}/index",
                    json={
                        "docs_dir": self.docs_dir,
                        "chunk_size": self.chunk_size,
                        "chunk_overlap": self.chunk_overlap
                    },
                    timeout=10.0
                )
                if response.status_code != 200:
                    self.indexing_status = f"Ошибка: {response.text}"
                    self.is_indexing = False
                    yield
                    return
        except Exception as e:
            self.indexing_status = f"Ошибка соединения: {str(e)}"
            self.is_indexing = False
            yield
            return

        # Polling loop
        while self.is_indexing:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"{API_URL}/index/progress")
                    data = resp.json()
                    
                    status = data.get("status", "")
                    message = data.get("message", "")
                    total = data.get("total", 0)
                    processed = data.get("processed", 0)
                    
                    if total > 0:
                        self.indexing_progress_val = int((processed / total) * 100)
                        self.indexing_status = f"{message} ({processed}/{total})"
                    else:
                        self.indexing_progress_val = 0
                        self.indexing_status = message
                        
                    yield
                    
                    if status in ["done", "error"]:
                        self.is_indexing = False
                        yield
                        break
            except Exception:
                pass
                
            await asyncio.sleep(1)
