from google import genai
from google.genai import types
from backend.core.config import settings
from fastembed import TextEmbedding

class LLMService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        # Локальная модель для векторизации (бесплатно и без лимитов!)
        self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        
    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        embeddings = list(self.embedding_model.embed(texts))
        return [emb.tolist() for emb in embeddings]

    def generate_answer(self, query: str, context: list[str], model: str = "gemini-2.5-flash") -> str:
        context_str = "\n\n".join(context)
        prompt = f"""
Вы — вежливый интеллектуальный помощник. 
Ваша задача — отвечать на вопросы пользователя, опираясь на предоставленный контекст.
Если пользователь просто здоровается, ответьте вежливо и предложите помощь.
Если задан вопрос по сути, но в контексте нет ответа, честно скажите, что не нашли информации в документах.

Контекст:
{context_str}

Запрос пользователя:
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
