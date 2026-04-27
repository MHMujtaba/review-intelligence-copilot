from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Review-Centric RAG Intelligence System", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    embedding_provider: str = Field(default="sentence-transformers", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")
    data_dir: Path = Field(default=BASE_DIR / "data", alias="DATA_DIR")
    vector_store_dir: Path = Field(default=BASE_DIR / "data" / "vector_store", alias="VECTOR_STORE_DIR")
    model_dir: Path = Field(default=BASE_DIR / "data" / "models", alias="MODEL_DIR")
    cache_file: Path = Field(default=BASE_DIR / "data" / "review_cache.json", alias="CACHE_FILE")
    semantic_top_k: int = Field(default=50, alias="SEMANTIC_TOP_K")
    retrieval_candidate_k: int = Field(default=50, alias="RETRIEVAL_CANDIDATE_K")
    rerank_top_k: int = Field(default=8, alias="RERANK_TOP_K")
    min_review_words: int = Field(default=8, alias="MIN_REVIEW_WORDS")
    min_helpfulness_ratio: float = Field(default=0.02, alias="MIN_HELPFULNESS_RATIO")
    near_duplicate_similarity: float = Field(default=0.9, alias="NEAR_DUPLICATE_SIMILARITY")
    quality_threshold: float = Field(default=0.75, alias="QUALITY_THRESHOLD")
    fallback_embedding_dimensions: int = 384


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.vector_store_dir.mkdir(parents=True, exist_ok=True)
    settings.model_dir.mkdir(parents=True, exist_ok=True)
    return settings
