from dataclasses import dataclass

import httpx
from openai import AsyncOpenAI

from app.core.config import settings
from app.repositories.documents import SearchResult


@dataclass(frozen=True)
class ChatAnswer:
    answer: str


class ChatService:
    def __init__(self):
        self.openai_client = (
            AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())
            if settings.has_openai_api_key
            else None
        )

    @property
    def is_enabled(self) -> bool:
        if settings.LLM_PROVIDER == "openai":
            return self.openai_client is not None
        if settings.LLM_PROVIDER == "ollama":
            return True
        return False

    def build_context(self, results: list[SearchResult]) -> str:
        blocks: list[str] = []
        current_size = 0

        for index, result in enumerate(results, start=1):
            block = (
                f"[{index}] Arquivo: {result.file_name}\n"
                f"Score: {result.score:.4f}\n"
                f"Trecho:\n{result.content.strip()}\n"
            )
            if current_size + len(block) > settings.CHAT_MAX_CONTEXT_CHARS:
                break
            blocks.append(block)
            current_size += len(block)

        return "\n---\n".join(blocks)

    def build_messages(self, question: str, results: list[SearchResult]) -> list[dict[str, str]]:
        context = self.build_context(results)
        return [
            {
                "role": "system",
                "content": (
                    "Voce e um assistente RAG corporativo. Responda em portugues, "
                    "use apenas o contexto fornecido e cite fontes no formato [1], [2]. "
                    "Se o contexto for insuficiente, diga isso claramente."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Pergunta:\n{question}\n\n"
                    f"Contexto recuperado:\n{context if context else 'Nenhum contexto recuperado.'}"
                ),
            },
        ]

    async def answer_question(
        self,
        *,
        question: str,
        results: list[SearchResult],
    ) -> ChatAnswer:
        if not self.is_enabled:
            raise RuntimeError("Chat requires a configured LLM provider.")

        messages = self.build_messages(question, results)
        if settings.LLM_PROVIDER == "openai":
            return await self._answer_with_openai(messages)
        if settings.LLM_PROVIDER == "ollama":
            return await self._answer_with_ollama(messages)

        raise RuntimeError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

    async def _answer_with_openai(self, messages: list[dict[str, str]]) -> ChatAnswer:
        if self.openai_client is None:
            raise RuntimeError("OpenAI chat requires OPENAI_API_KEY to be configured.")

        response = await self.openai_client.chat.completions.create(
            model=settings.LLM_MODEL,
            temperature=settings.TEMPERATURE,
            messages=messages,
        )
        message = response.choices[0].message.content or ""
        return ChatAnswer(answer=message.strip())

    async def _answer_with_ollama(self, messages: list[dict[str, str]]) -> ChatAnswer:
        try:
            async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=120.0) as client:
                response = await client.post(
                    "/api/chat",
                    json={
                        "model": settings.LLM_MODEL,
                        "messages": messages,
                        "stream": False,
                        "options": {"temperature": settings.TEMPERATURE},
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                "Ollama chat provider unavailable. Start Ollama and run "
                f"`ollama pull {settings.LLM_MODEL}`."
            ) from exc

        payload = response.json()
        message = payload.get("message", {}).get("content", "")
        return ChatAnswer(answer=message.strip())


chat_service = ChatService()
