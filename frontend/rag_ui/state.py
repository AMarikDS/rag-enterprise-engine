import reflex as rx
import httpx
import os
from pydantic import BaseModel
from typing import List

API_URL = os.getenv("API_URL", "http://localhost:8080/api")


class ChatMessage(BaseModel):
    text: str
    is_user: bool
    sources: List[str] = []
    image: str = ""


class SessionData(BaseModel):
    id: str
    name: str
    kb_name: str


class State(rx.State):
    # Chat State
    chat_history: list[ChatMessage] = []
    current_query: str = ""
    is_loading: bool = False
    image_data: str = ""
    file_name: str = ""

    # KB & Sessions State
    kbs: list[str] = []
    sessions: list[dict] = []  # list of {id, name, kb_name}
    current_session_id: str = ""
    current_kb_name: str = ""
    new_kb_name: str = ""
    new_session_name: str = ""

    # Settings State
    docs_dir: str = "/app/docs"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    selected_model: str = "gemini-3.6-flash"
    available_models: list[str] = [
        "gemini-3.7-flash (⚡️ Рекомендуемая, быстрая, топ для бесплатного тарифа)",
        "gemini-2.5-pro (🧠 Мощная, но жесткие лимиты без подписки)",
        "gemini-3.6-flash (Стабильная)",
        "gemini-flash-latest (Автообновляемая)",
    ]

    indexing_progress_val: int = 0
    indexing_status: str = ""
    is_indexing: bool = False

    def set_current_query(self, value: str):
        self.current_query = value

    def set_docs_dir(self, value: str):
        self.docs_dir = value

    def set_new_kb_name(self, value: str):
        self.new_kb_name = value

    def set_current_kb_name(self, value: str):
        self.current_kb_name = value

    def set_new_session_name(self, value: str):
        self.new_session_name = value

    async def init_data(self):
        await self.load_kbs()
        await self.load_sessions()

    async def load_kbs(self):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{API_URL}/kb")
                if resp.status_code == 200:
                    self.kbs = resp.json().get("kbs", [])
        except Exception:
            self.kbs = []

    async def load_sessions(self):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{API_URL}/sessions")
                if resp.status_code == 200:
                    self.sessions = resp.json().get("sessions", [])
                    if self.sessions and not self.current_session_id:
                        await self.select_session(self.sessions[0]["id"])
        except Exception:
            self.sessions = []

    async def select_session(self, session_id: str):
        self.current_session_id = session_id
        for s in self.sessions:
            if s["id"] == session_id:
                self.current_kb_name = s.get("kb_name", "")
                actual_model = s.get("model", "gemini-3.6-flash")
                self.selected_model = self.available_models[0]
                for m in self.available_models:
                    if m.startswith(actual_model):
                        self.selected_model = m
                        break
                break
        await self.load_history()
        return rx.call_script(
            "setTimeout(() => { var el = document.getElementById('chat_history_box'); if(el) el.scrollTop = el.scrollHeight; }, 100);"
        )

    async def create_session(self):
        if not self.new_session_name or not self.current_kb_name:
            return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{API_URL}/sessions",
                    json={
                        "name": self.new_session_name,
                        "kb_name": self.current_kb_name,
                        "model": self.selected_model.split(" ")[0],
                    },
                )
                if resp.status_code == 200:
                    session_id = resp.json().get("session_id")
                    self.new_session_name = ""
                    await self.load_sessions()
                    await self.select_session(session_id)
        except Exception:
            pass

    async def delete_session(self, session_id: str):
        try:
            async with httpx.AsyncClient() as client:
                await client.delete(f"{API_URL}/sessions/{session_id}")
            if self.current_session_id == session_id:
                self.current_session_id = ""
                self.chat_history = []
            await self.load_sessions()
        except Exception:
            pass

    async def update_selected_model(self, model: str):
        self.selected_model = model
        if self.current_session_id:
            try:
                actual_model = model.split(" ")[0]
                async with httpx.AsyncClient() as client:
                    await client.patch(
                        f"{API_URL}/sessions/{self.current_session_id}/model",
                        json={"model": actual_model},
                    )
            except Exception as e:
                print(f"Failed to update session model: {e}")

    async def delete_kb(self, kb_name: str):
        try:
            async with httpx.AsyncClient() as client:
                await client.delete(f"{API_URL}/kb/{kb_name}")
            await self.load_kbs()
        except Exception:
            pass

    async def load_history(self):
        if not self.current_session_id:
            self.chat_history = []
            return
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_URL}/history", params={"session_id": self.current_session_id}
                )
                if response.status_code == 200:
                    data = response.json().get("history", [])
                    self.chat_history = [
                        ChatMessage(
                            text=m["text"],
                            is_user=m["is_user"],
                            sources=m.get("sources", []),
                            image=m.get("image", ""),
                        )
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

    def on_key_down(self, key: str, shift_key: bool):
        if key == "Enter" and not shift_key:
            return State.send_message()

    async def handle_upload(self, files: list[rx.UploadFile]):
        for file in files:
            upload_data = await file.read()
            import base64
            import urllib.parse
            b64 = base64.b64encode(upload_data).decode('utf-8')
            content_type = getattr(file, "content_type", "application/octet-stream")
            # reflex upload files usually have filename attribute
            filename = getattr(file, "filename", getattr(file, "name", "document"))
            self.file_name = filename
            # Encode filename to be safe in URI
            safe_filename = urllib.parse.quote(filename)
            self.image_data = f"data:{content_type};name={safe_filename};base64,{b64}"
            break

    def clear_image(self):
        self.image_data = ""
        self.file_name = ""

    async def _save_message_to_backend(self, msg: ChatMessage):
        if not self.current_session_id:
            return
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{API_URL}/history",
                    json={
                        "session_id": self.current_session_id,
                        "message": {
                            "text": msg.text,
                            "is_user": msg.is_user,
                            "sources": msg.sources,
                            "image": msg.image,
                        },
                    },
                )
        except Exception:
            pass

    async def send_message_form(self, form_data: dict):
        query = form_data.get("query", "")
        if not query.strip() or not self.current_session_id:
            return

        self.current_query = ""
        user_msg = ChatMessage(text=query, is_user=True, image=self.image_data)
        
        # Save image data for API call and clear state immediately for UI responsiveness
        current_image_data = self.image_data
        self.image_data = ""
        
        self.chat_history.append(user_msg)
        await self._save_message_to_backend(user_msg)

        self.is_loading = True
        yield rx.call_script(
            "setTimeout(() => { var el = document.getElementById('chat_history_box'); if(el) el.scrollTop = el.scrollHeight; }, 100);"
        )
        yield rx.set_value("query_input", "")
        yield rx.call_script(
            "setTimeout(() => { var el = document.getElementById('query_input'); if(el) { var setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set; setter.call(el, ''); el.dispatchEvent(new Event('input', { bubbles: true })); el.style.removeProperty('height'); } }, 50);"
        )

        try:
            async with httpx.AsyncClient() as client:
                actual_model = self.selected_model.split(" ")[0]
                response = await client.post(
                    f"{API_URL}/chat",
                    json={
                        "query": query,
                        "model": actual_model,
                        "session_id": self.current_session_id,
                        "kb_name": self.current_kb_name,
                        "image_base64": current_image_data if current_image_data else None,
                    },
                    timeout=120.0,
                )
                if response.status_code != 200:
                    try:
                        err_detail = response.json().get("detail", response.text)
                    except Exception:
                        err_detail = response.text
                    err_msg = (
                        str(err_detail)
                        if str(err_detail).strip()
                        else "Unknown API Error"
                    )
                    raise Exception(err_msg)

                data = response.json()

                bot_msg = ChatMessage(
                    text=data["answer"], is_user=False, sources=data.get("sources", [])
                )
                self.chat_history.append(bot_msg)
                await self._save_message_to_backend(bot_msg)
        except Exception as e:
            err_msg_text = str(e).strip()
            if not err_msg_text:
                err_msg_text = repr(e)
            err_msg = ChatMessage(text=f"Error: {err_msg_text}", is_user=False)
            self.chat_history.append(err_msg)
            await self._save_message_to_backend(err_msg)
        finally:
            self.is_loading = False
            yield rx.call_script(
                "setTimeout(() => { var el = document.getElementById('chat_history_box'); if(el) el.scrollTop = el.scrollHeight; }, 100);"
            )

    async def start_indexing(self):
        if not self.new_kb_name.strip():
            self.indexing_status = "Укажите имя базы знаний!"
            return

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
                        "kb_name": self.new_kb_name,
                        "docs_dir": self.docs_dir,
                        "chunk_size": self.chunk_size,
                        "chunk_overlap": self.chunk_overlap,
                    },
                    timeout=30.0,
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
                        await self.load_kbs()
                        self.new_kb_name = ""
                        yield
                        break
            except Exception:
                pass

            await asyncio.sleep(1)
