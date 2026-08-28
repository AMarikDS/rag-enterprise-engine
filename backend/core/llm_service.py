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
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                    ),
                )
                return response.text
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)  # 1s, 2s, 4s


llm_service = LLMService()
