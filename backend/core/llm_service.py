from google import genai
from google.genai import types
from backend.core.config import settings
from fastembed import TextEmbedding


class LLMService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        # Мультиязычная модель для векторизации (отлично понимает и РУ, и АНГЛ)
        self.embedding_model = TextEmbedding(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        embeddings = list(self.embedding_model.embed(texts))
        return [emb.tolist() for emb in embeddings]

    def generate_answer(
        self,
        query: str,
        context: list[str],
        model: str = "gemini-3.6-flash",
        history: list[dict] = None,
        image_base64: str = None,
    ) -> str:
        context_str = "\n\n".join(context)
        history_str = ""
        if history:
            for msg in history:
                role = "Пользователь" if msg.get("is_user") else "Ассистент"
                history_str += f"{role}: {msg.get('text')}\n"

        prompt = f"""
Вы — интеллектуальный помощник, эксперт по анализу документов.
Ваша задача — максимально подробно, профессионально и структурированно отвечать на вопросы пользователя, опираясь исключительно на предоставленный контекст и историю диалога.

Правила:
1. Ведите диалог естественно. НЕ здоровайтесь в каждом сообщении.
2. Отвечайте развернуто, используйте абзацы, списки и выделения жирным шрифтом для ключевых терминов, чтобы текст легко читался.
3. Если информации в контексте нет, прямо скажите об этом, но постарайтесь ответить на ту часть вопроса, которая покрывается базой знаний.

История диалога (последние сообщения):
{history_str if history_str else "Нет (это начало диалога)"}

Контекст из базы знаний:
{context_str if context_str else "Контекст не найден."}

Текущий запрос пользователя:
{query}
"""
        contents = [prompt]
        if image_base64:
            import base64
            import re
            import urllib.parse

            mime_type = "image/jpeg"
            b64_data = image_base64
            file_name = "document"

            # format is data:content_type;name=encoded_name;base64,data
            # or data:content_type;base64,data
            match = re.match(r"data:(.*?);(.*?)base64,(.*)", image_base64)
            if match:
                mime_type = match.group(1)
                middle = match.group(2)
                b64_data = match.group(3)

                if middle.startswith("name="):
                    name_part = middle[5:].rstrip(";")
                    file_name = urllib.parse.unquote(name_part)

            try:
                file_bytes = base64.b64decode(b64_data)

                if mime_type.startswith("image/") or mime_type == "application/pdf":
                    contents.append(
                        types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
                    )
                elif (
                    mime_type
                    == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                ):
                    import docx
                    import io

                    doc = docx.Document(io.BytesIO(file_bytes))
                    full_text = []
                    for para in doc.paragraphs:
                        full_text.append(para.text)
                    decoded_text = "\n".join(full_text)
                    prompt_addition = f"\n\n--- Содержимое прикрепленного документа ({file_name}) ---\n{decoded_text}\n--- Конец документа ---"
                    contents[0] += prompt_addition
                else:
                    # Treat as text
                    decoded_text = file_bytes.decode("utf-8", errors="replace")
                    prompt_addition = f"\n\n--- Содержимое прикрепленного файла ({file_name}) ---\n{decoded_text}\n--- Конец файла ---"
                    contents[0] += prompt_addition
            except Exception as e:
                print(f"Failed to decode or attach file: {e}")

        import time

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                    ),
                )
                return response.text
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2**attempt)  # 1s, 2s, 4s


llm_service = LLMService()
