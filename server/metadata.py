import os
import json
from dotenv import load_dotenv
from google import genai
from server.schemas import DocumentMetadata

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")

_client = None

def _get_client():
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in .env")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client

def extract_metadata(content: str) -> DocumentMetadata:
    """
    Extract structured metadata from the document content using Gemini API.
    Truncates content to the first 8000 characters to save tokens.
    """
    if not content or not content.strip():
        # Fallback empty metadata if there's no text
        return DocumentMetadata(
            title="Unknown Title",
            summary="No content provided.",
            topics=[],
            document_type="unknown",
            language="en"
        )
        
    client = _get_client()
    
    # Take first 8000 chars to avoid exceeding context or costing too much
    truncated_content = content[:8000]

    system_instruction = (
        "You are an expert document analyzer. Extract the title, a brief summary, "
        "a list of key topics, the document type (e.g., 'article', 'report', 'notes', 'technical documentation'), "
        "and the 2-letter ISO language code for the following text. "
        "Do not invent information. If you cannot determine the title, use the first sentence."
    )
    
    response = client.models.generate_content(
        model=GEMINI_CHAT_MODEL,
        contents=f"{system_instruction}\n\nDocument Text:\n{truncated_content}",
        config=dict(
            response_mime_type="application/json",
            response_schema=DocumentMetadata,
            temperature=0.0
        )
    )
    
    # Parse the json string from the response into our Pydantic schema
    try:
        # Pydantic v2 validation from JSON string
        raw_json = response.text
        return DocumentMetadata.model_validate_json(raw_json)
    except Exception as e:
        # Fallback to defaults on parse failure
        return DocumentMetadata(
            title="Parsing Error",
            summary=f"Failed to parse metadata: {str(e)}",
            topics=[],
            document_type="unknown",
            language="en"
        )
