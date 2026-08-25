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

    def set_current_query(self, value: str):
        self.current_query = value

    def set_docs_dir(self, value: str):
        self.docs_dir = value

    async def load_history(self):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_URL}/history", params={"docs_dir": self.docs_dir})
                if response.status_code == 200:
                    data = response.json().get("history", [])
                    self.chat_history = [
                        ChatMessage(text=m["text"], is_user=m["is_user"], sources=m.get("sources", []))
                        for m in data
                    ]
                else:
                    self.chat_history = []
        except Exception:
            pass

    def set_chunk_size(self, value: int | list[int]):
        self.chunk_size = value[0] if isinstance(value, list) else value

    def set_chunk_overlap(self, value: int | list[int]):
        self.chunk_overlap = value[0] if isinstance(value, list) else value

    def set_selected_model(self, value: str):
        self.selected_model = value

    def on_key_down(self, key: str):
        if key == "Enter":
            return State.send_message()

    async def _save_message_to_backend(self, msg: ChatMessage):
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{API_URL}/history",
                    json={
                        "docs_dir": self.docs_dir,
                        "message": {"text": msg.text, "is_user": msg.is_user, "sources": msg.sources}
                    }
                )
        except Exception:
            pass

    async def send_message(self):
        if not self.current_query.strip():
            return
            
        query = self.current_query
        self.current_query = ""
        user_msg = ChatMessage(text=query, is_user=True)
        self.chat_history.append(user_msg)
        await self._save_message_to_backend(user_msg)
        
        self.is_loading = True
        yield
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_URL}/chat", 
                    json={"query": query, "model": self.selected_model},
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                bot_msg = ChatMessage(
                    text=data["answer"], 
                    is_user=False, 
                    sources=data.get("sources", [])
                )
                self.chat_history.append(bot_msg)
                await self._save_message_to_backend(bot_msg)
        except Exception as e:
            err_msg = ChatMessage(text=f"Error: {str(e)}", is_user=False)
            self.chat_history.append(err_msg)
            await self._save_message_to_backend(err_msg)
        finally:
            self.is_loading = False

    async def update_settings(self):
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{API_URL}/settings",
                    json={
                        "docs_dir": self.docs_dir,
                        "chunk_size": self.chunk_size,
                        "chunk_overlap": self.chunk_overlap
                    }
                )
            # Load history just in case the directory was changed
            await self.load_history()
        except Exception as e:
            print(f"Failed to update settings: {e}")

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
