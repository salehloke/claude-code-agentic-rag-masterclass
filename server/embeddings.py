import os
import ollama
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """
    Embed a batch of texts via Ollama.
    Returns a list of embedding vectors (one per input text).
    """
    client = ollama.Client(host=OLLAMA_BASE_URL)
    response = client.embed(model=OLLAMA_EMBEDDING_MODEL, input=texts)
    return response.embeddings


def embed_text(text: str, task_type: str = "RETRIEVAL_QUERY") -> list[float]:
    """Embed a single text string."""
    return embed_texts([text], task_type=task_type)[0]


def embed_chunks_with_context(
    full_document: str,
    chunks: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[list[float]]:
    """Route chunk embedding through the configured provider.
    Only jina_late uses full_document; ollama calls embed_texts() as before."""
    provider = os.getenv("EMBEDDING_PROVIDER", "ollama")
    if provider == "jina_late":
        from server.late_chunking import late_chunk_embed
        return late_chunk_embed(full_document, chunks)
    return embed_texts(chunks, task_type=task_type)
