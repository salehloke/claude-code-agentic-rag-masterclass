import os
import json
import ollama
from dotenv import load_dotenv
from server.schemas import DocumentMetadata

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5:3b")


def extract_metadata(content: str) -> DocumentMetadata:
    """
    Extract structured metadata from document content using a local Ollama model.
    Truncates content to the first 8000 characters to save tokens.
    """
    if not content or not content.strip():
        return DocumentMetadata(
            title="Unknown Title",
            summary="No content provided.",
            topics=[],
            document_type="unknown",
            language="en",
            project=None,
        )

    truncated_content = content[:8000]
    schema = DocumentMetadata.model_json_schema()

    prompt = (
        "You are an expert document analyzer. Extract structured metadata from the document below.\n"
        "Return a JSON object matching this schema:\n"
        f"{json.dumps(schema, indent=2)}\n\n"
        "Rules:\n"
        "- title: document title, or first sentence if unclear\n"
        "- summary: brief 1-2 sentence summary\n"
        "- topics: list of key topics\n"
        "- document_type: one of 'article', 'report', 'notes', 'technical documentation'\n"
        "- language: 2-letter ISO code (e.g. 'en')\n"
        "- project: project or product name this document belongs to, or null if unclear\n\n"
        f"Document:\n{truncated_content}"
    )

    client = ollama.Client(host=OLLAMA_BASE_URL)
    response = client.chat(
        model=OLLAMA_CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        format="json",
        options={"temperature": 0.0},
    )

    try:
        raw_json = response.message.content
        return DocumentMetadata.model_validate_json(raw_json)
    except Exception as e:
        return DocumentMetadata(
            title="Parsing Error",
            summary=f"Failed to parse metadata: {str(e)}",
            topics=[],
            document_type="unknown",
            language="en",
            project=None,
        )
