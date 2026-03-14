import os
import ollama
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_RERANKER_MODEL = os.getenv("OLLAMA_RERANKER_MODEL", "bbjson/bge-reranker-base")


def rerank_results(query: str, results: list[dict], top_k: int = 5) -> list[dict]:
    """Rerank a list of candidate results using Ollama rerank API."""
    if not results:
        return results

    client = ollama.Client(host=OLLAMA_BASE_URL)
    documents = [doc["content"] for doc in results]

    response = client.rerank(model=OLLAMA_RERANKER_MODEL, query=query, documents=documents)

    for rank_result in response.results:
        results[rank_result.index]["reranker_score"] = rank_result.relevance_score

    reranked = sorted(results, key=lambda x: x["reranker_score"], reverse=True)
    return reranked[:top_k]
