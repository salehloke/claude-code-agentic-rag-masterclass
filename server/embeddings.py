import os
from dotenv import load_dotenv
from google import genai
from google.genai.types import EmbedContentConfig

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
GEMINI_EMBEDDING_DIMENSIONS = int(os.getenv("GEMINI_EMBEDDING_DIMENSIONS", "768"))

_client = None


def _get_client():
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in .env")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """
    Embed a batch of texts via Gemini API.
    Returns a list of embedding vectors (one per input text).

    Args:
        texts: List of text strings to embed.
        task_type: Embedding task type. Use "RETRIEVAL_DOCUMENT" for ingestion,
                   "RETRIEVAL_QUERY" for search queries.
    """
    client = _get_client()
    response = client.models.embed_content(
        model=GEMINI_EMBEDDING_MODEL,
        contents=texts,
        config=EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=GEMINI_EMBEDDING_DIMENSIONS,
        ),
    )
    return [e.values for e in response.embeddings]


def embed_text(text: str, task_type: str = "RETRIEVAL_QUERY") -> list[float]:
    """Embed a single text string. Defaults to RETRIEVAL_QUERY for search queries."""
    return embed_texts([text], task_type=task_type)[0]


def embed_chunks_with_context(
    full_document: str,
    chunks: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[list[float]]:
    """Route chunk embedding through the configured provider.
    Only jina_late uses full_document; gemini/ollama call embed_texts() as before."""
    import os
    provider = os.getenv("EMBEDDING_PROVIDER", "gemini")
    if provider == "jina_late":
        from server.late_chunking import late_chunk_embed
        return late_chunk_embed(full_document, chunks)
    return embed_texts(chunks, task_type=task_type)
