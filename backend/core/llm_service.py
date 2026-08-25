from google import genai
from google.genai import types
from backend.core.config import settings
from fastembed import TextEmbedding

class LLMService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        # Мультиязычная модель для векторизации (отлично понимает и РУ, и АНГЛ)
        self.embedding_model = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        
    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        embeddings = list(self.embedding_model.embed(texts))
        return [emb.tolist() for emb in embeddings]

    def generate_answer(self, query: str, context: list[str], model: str = "gemini-3.6-flash", history: list[dict] = None) -> str:
        context_str = "\n\n".join(context)
        history_str = ""
        if history:
            for msg in history:
                role = "Пользователь" if msg.get("is_user") else "Ассистент"
                history_str += f"{role}: {msg.get('text')}\n"
                
        prompt = f"""
Вы — интеллектуальный помощник.
Ваша задача — отвечать на вопросы пользователя, опираясь на предоставленный контекст и историю диалога.
Ведите диалог естественно. НЕ здоровайтесь в каждом сообщении.

История диалога (последние сообщения):
{history_str if history_str else "Нет (это начало диалога)"}

Контекст из базы знаний:
{context_str if context_str else "Контекст не найден."}

Текущий запрос пользователя:
{query}
"""
        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
            )
        )
        return response.text

llm_service = LLMService()
