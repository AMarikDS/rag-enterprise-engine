import reflex as rx
import httpx
import os
from pydantic import BaseModel
from typing import List

API_URL = "http://localhost:8000/api"

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
    
    indexing_status: str = ""
    is_indexing: bool = False

    def set_current_query(self, value: str):
        self.current_query = value

    def set_docs_dir(self, value: str):
        self.docs_dir = value

    def set_chunk_size(self, value: int | list[int]):
        self.chunk_size = value[0] if isinstance(value, list) else value

    def set_chunk_overlap(self, value: int | list[int]):
        self.chunk_overlap = value[0] if isinstance(value, list) else value

    def set_selected_model(self, value: str):
        self.selected_model = value
    async def send_message(self):
        if not self.current_query.strip():
            return
            
        query = self.current_query
        self.current_query = ""
        self.chat_history.append(ChatMessage(text=query, is_user=True))
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
                
                self.chat_history.append(
                    ChatMessage(
                        text=data["answer"], 
                        is_user=False, 
                        sources=data.get("sources", [])
                    )
                )
        except Exception as e:
            self.chat_history.append(
                ChatMessage(
                    text=f"Error: {str(e)}", 
                    is_user=False
                )
            )
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
        except Exception as e:
            print(f"Failed to update settings: {e}")

    async def start_indexing(self):
        self.is_indexing = True
        self.indexing_status = "Индексация запущена..."
        yield
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_URL}/index",
                    json={
                        "docs_dir": self.docs_dir,
                        "chunk_size": self.chunk_size,
                        "chunk_overlap": self.chunk_overlap
                    },
                    timeout=300.0
                )
                if response.status_code == 200:
                    data = response.json()
                    self.indexing_status = data.get("message", "Успешно проиндексировано.")
                else:
                    self.indexing_status = f"Ошибка: {response.text}"
        except Exception as e:
            self.indexing_status = f"Ошибка соединения: {str(e)}"
        finally:
            self.is_indexing = False
