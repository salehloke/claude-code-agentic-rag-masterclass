import os
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from supabase import create_client

from server.chunking import recursive_split
from server.embeddings import embed_texts, embed_text
from server.metadata import extract_metadata
from server.parser import parse_document

load_dotenv()

mcp = FastMCP("rag-masterclass")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def _get_supabase():
    """Get a Supabase client instance."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


@mcp.tool()
def hello(name: str = "world") -> str:
    """Say hello — verifies the MCP server is working."""
    return f"Hello, {name}! RAG Masterclass MCP server is running."


@mcp.tool()
def supabase_health() -> dict:
    """Check Supabase local stack connectivity."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return {"status": "error", "message": "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env"}

    try:
        client = _get_supabase()
        users = client.auth.admin.list_users()
        return {
            "status": "connected",
            "supabase_url": SUPABASE_URL,
            "auth_users_count": len(users) if users else 0,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def ingest_file(file_path: str, force: bool = False) -> dict:
    """Ingest a file: read → chunk → embed → store in pgvector.

    Skips ingestion if content is unchanged (same hash). If the same filename
    exists with a different hash, the old document is deleted and re-ingested.
    Use force=True to re-ingest even when the hash matches.

    Args:
        file_path: Absolute or relative path to the file to ingest.
        force: Re-ingest even if content hash is unchanged (default False).
    """
    path = Path(file_path).resolve()
    if not path.exists():
        return {"status": "error", "message": f"File not found: {path}"}

    try:
        content = parse_document(str(path))
    except Exception as e:
        return {"status": "error", "message": f"Failed to parse document: {str(e)}"}
        
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    filename = path.name

    client = _get_supabase()

    # Check for existing document with same filename
    same_name_result = client.table("documents").select("id, content_hash").eq(
        "filename", filename
    ).execute()

    if same_name_result.data:
        existing = same_name_result.data[0]
        if existing["content_hash"] == content_hash and not force:
            # Same content — skip
            return {
                "status": "skipped",
                "reason": "duplicate",
                "existing_document_id": existing["id"],
                "filename": filename,
            }
        else:
            # Same filename, different hash (or force=True) — delete old and re-ingest
            old_id = existing["id"]
            storage_path = f"documents/{old_id}/{filename}"
            try:
                client.storage.from_("documents").remove([storage_path])
            except Exception:
                pass
            client.table("documents").delete().eq("id", old_id).execute()

    # Create document record
    doc_result = client.table("documents").insert({
        "filename": filename,
        "file_path": str(path),
        "content_hash": content_hash,
        "status": "processing",
    }).execute()

    doc_id = doc_result.data[0]["id"]

    try:
        # Upload raw file to Supabase Storage
        storage_path = f"documents/{doc_id}/{filename}"
        
        # Map file extensions to appropriate MIME types for Supabase Storage
        mime_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".html": "text/html",
            ".md": "text/markdown",
            ".txt": "text/plain"
        }
        content_type = mime_types.get(path.suffix.lower(), "application/octet-stream")
        
        with open(path, "rb") as f:
            client.storage.from_("documents").upload(
                storage_path,
                f.read(),
                {"content-type": content_type},
            )

        # Chunk the content
        chunks = recursive_split(content)

        if not chunks:
            client.table("documents").update({
                "status": "failed",
            }).eq("id", doc_id).execute()
            return {"status": "error", "message": "No chunks produced from file"}

        # Batch embed all chunks
        embeddings = embed_texts(chunks)

        # Insert chunks with embeddings
        chunk_records = []
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_records.append({
                "document_id": doc_id,
                "content": chunk_text,
                "embedding": embedding,
                "chunk_index": i,
                "token_count": len(chunk_text.split()),
            })

        client.table("chunks").insert(chunk_records).execute()

        # Extract metadata
        try:
            metadata = extract_metadata(content)
        except Exception as e:
            # Fallback if LLM extraction completely blows up
            metadata = None
            print(f"Warning: Metadata extraction failed. {e}")

        # Update document status and metadata
        update_data = {
            "status": "completed",
            "chunk_count": len(chunks),
        }
        
        if metadata:
            update_data.update({
                "title": metadata.title,
                "summary": metadata.summary,
                "topics": metadata.topics,
                "document_type": metadata.document_type,
                "language": metadata.language,
            })

        client.table("documents").update(update_data).eq("id", doc_id).execute()

        return {
            "status": "completed",
            "document_id": doc_id,
            "filename": filename,
            "chunk_count": len(chunks),
            "content_hash": content_hash,
            "metadata_extracted": metadata is not None,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        client.table("documents").update({
            "status": "failed",
        }).eq("id", doc_id).execute()
        return {"status": "error", "document_id": doc_id, "message": str(e)}


@mcp.tool()
def list_documents() -> list[dict]:
    """List all ingested documents with their status and chunk count."""
    client = _get_supabase()
    result = client.table("documents").select(
        "id, filename, status, chunk_count, content_hash, created_at"
    ).order("created_at", desc=True).execute()
    return result.data


@mcp.tool()
def delete_document(document_id: str) -> dict:
    """Delete a document and all its chunks (cascade delete).

    Args:
        document_id: UUID of the document to delete.
    """
    client = _get_supabase()

    # Get document info first
    doc = client.table("documents").select("id, filename").eq(
        "id", document_id
    ).single().execute()

    if not doc.data:
        return {"status": "error", "message": f"Document not found: {document_id}"}

    filename = doc.data["filename"]

    # Delete from storage
    storage_path = f"documents/{document_id}/{filename}"
    try:
        client.storage.from_("documents").remove([storage_path])
    except Exception:
        pass  # File may not exist in storage

    # Delete document (chunks cascade via FK)
    client.table("documents").delete().eq("id", document_id).execute()

    return {
        "deleted": True,
        "document_id": document_id,
        "filename": filename,
    }


@mcp.tool()
def search_documents(
    query: str, 
    top_k: int = 5, 
    threshold: float = 0.7,
    document_type: str | None = None,
    topics: list[str] | None = None
) -> list[dict]:
    """Search ingested documents using vector similarity and optional metadata filters.

    Args:
        query: The search query text.
        top_k: Number of results to return (default 5).
        threshold: Minimum similarity score 0-1 (default 0.7).
        document_type: Filter by a specific document type (e.g., 'article', 'report').
        topics: Filter to documents containing at least one of these topics.
    """
    client = _get_supabase()
    
    # 1. Embed the search query
    try:
        query_embedding = embed_text(query, task_type="RETRIEVAL_QUERY")
    except Exception as e:
        return [{"error": f"Failed to embed query: {str(e)}"}]
        
    # 2. Call the Supabase RPC function for vector search
    try:
        response = client.rpc(
            "search_chunks",
            {
                "query_embedding": query_embedding,
                "match_count": top_k,
                "match_threshold": threshold,
                "filter_document_type": document_type,
                "filter_topics": topics
            }
        ).execute()
        
        results = response.data
        
        if not results:
            return [{"message": f"No relevant chunks found above similarity threshold {threshold}."}]
            
        return results
        
    except Exception as e:
        return [{"error": f"Database search failed: {str(e)}"}]


if __name__ == "__main__":
    mcp.run(transport="stdio")
