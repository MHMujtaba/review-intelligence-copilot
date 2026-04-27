import asyncio

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.preprocessing import normalize

from app.core.config import get_settings


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._sentence_model = None
        self._openai_client = None
        self._hashing_vectorizer = HashingVectorizer(
            n_features=self.settings.fallback_embedding_dimensions,
            alternate_sign=False,
            norm=None,
        )

    async def _load_sentence_model(self):
        if self._sentence_model is not None:
            return self._sentence_model
        from sentence_transformers import SentenceTransformer

        self._sentence_model = await asyncio.to_thread(SentenceTransformer, self.settings.embedding_model)
        return self._sentence_model

    async def _load_openai_client(self):
        if self._openai_client is not None:
            return self._openai_client
        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI embedding provider.")
        from openai import AsyncOpenAI

        self._openai_client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        return self._openai_client

    async def embed_texts(self, texts: list[str]) -> np.ndarray:
        provider = self.settings.embedding_provider.lower()
        if provider == "openai":
            return await self._embed_openai(texts)
        if provider == "sentence-transformers":
            try:
                return await self._embed_sentence_transformers(texts)
            except Exception:
                return self._embed_hashing(texts)
        return self._embed_hashing(texts)

    async def embed_query(self, text: str) -> np.ndarray:
        embeddings = await self.embed_texts([text])
        return embeddings[0]

    async def _embed_sentence_transformers(self, texts: list[str]) -> np.ndarray:
        model = await self._load_sentence_model()
        vectors = await asyncio.to_thread(model.encode, texts, normalize_embeddings=True)
        return np.asarray(vectors, dtype=np.float32)

    async def _embed_openai(self, texts: list[str]) -> np.ndarray:
        client = await self._load_openai_client()
        response = await client.embeddings.create(model="text-embedding-3-small", input=texts)
        vectors = np.asarray([item.embedding for item in response.data], dtype=np.float32)
        return normalize(vectors)

    def _embed_hashing(self, texts: list[str]) -> np.ndarray:
        matrix = self._hashing_vectorizer.transform(texts)
        dense = matrix.toarray().astype(np.float32)
        return normalize(dense)
