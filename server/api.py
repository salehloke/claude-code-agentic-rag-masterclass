import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from supabase import create_client, Client
import httpx
from pydantic import BaseModel
import ollama
import tempfile
from fastapi import UploadFile, File

from server.main import search_documents, ingest_file, list_documents, delete_document

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")  # Usually the frontend uses anon key, but backend can use anon to verify JWTs

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    # Fallback to service role if anon key isn't provided directly 
    # (Though anon key is ideal for passing user JWTs)
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get authenticated Supabase client for the current user
async def get_supabase_client(authorization: str = Header(None)) -> Client:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    token = authorization.split(" ")[1] if authorization.startswith("Bearer ") else authorization
    
    # Create client configured with the user's JWT
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.postgrest.auth(token)
    
    # Verify the user is real by fetching their data
    try:
        user_response = client.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")
        
    # We attach the user object to the client for convenience
    client.user = user_response.user
    return client

class ChatRequest(BaseModel):
    thread_id: str
    message: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest, client: Client = Depends(get_supabase_client)):
    # 1. Save the user's message to the database
    client.table("messages").insert({
        "thread_id": request.thread_id,
        "user_id": client.user.id,
        "role": "user",
        "content": request.message
    }).execute()
    
    # 2. Retrieve context via our existing RAG search (using default hybrid config)
    context_results = search_documents(request.message, top_k=5)
    
    context_texts = []
    if context_results and not "error" in context_results[0] and not "message" in context_results[0]:
        for res in context_results:
            context_texts.append(res.get("content", ""))
            
    context_block = "\n---\n".join(context_texts)
    
    # 3. Fetch conversation history for this thread
    history_response = client.table("messages").select("role, content").eq(
        "thread_id", request.thread_id
    ).order("created_at", desc=False).execute()
    
    messages = [
        {"role": "system", "content": f"You are a helpful assistant. Use the following context to answer the user's question. If the answer is not in the context, say you don't know.\n\nContext:\n{context_block}"}
    ]
    
    for msg in history_response.data:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    # 4. Stream response from local Ollama model
    async def generate():
        ollama_client = ollama.AsyncClient()
        response = await ollama_client.chat(
            model='qwen2.5:3b',
            messages=messages,
            stream=True
        )
        
        full_response = ""
        async for chunk in response:
            content = chunk['message']['content']
            full_response += content
            # SSE format
            yield f"data: {json.dumps({'content': content})}\n\n"
            
        # 5. Save the assistant's message to the DB after streaming completes
        if full_response:
             client.table("messages").insert({
                 "thread_id": request.thread_id,
                 "user_id": client.user.id,
                 "role": "assistant",
                 "content": full_response
             }).execute()
             
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

class ThreadCreate(BaseModel):
    title: str

@app.post("/threads")
async def create_thread(req: ThreadCreate, client: Client = Depends(get_supabase_client)):
    res = client.table("threads").insert({
        "user_id": client.user.id,
        "title": req.title
    }).execute()
    return res.data[0]

@app.get("/threads")
async def get_threads(client: Client = Depends(get_supabase_client)):
    res = client.table("threads").select("*").order("created_at", desc=True).execute()
    return res.data

@app.get("/threads/{thread_id}/messages")
async def get_messages(thread_id: str, client: Client = Depends(get_supabase_client)):
    res = client.table("messages").select("*").eq("thread_id", thread_id).order("created_at", desc=False).execute()
    return res.data

@app.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str, client: Client = Depends(get_supabase_client)):
    client.table("threads").delete().eq("id", thread_id).execute()
    return {"status": "deleted"}

@app.post("/ingest")
async def ingest_upload(file: UploadFile = File(...), client: Client = Depends(get_supabase_client)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    
    # Ingest the file using the core function
    res = ingest_file(tmp_path)
    os.remove(tmp_path)
    return res

@app.get("/documents")
async def get_all_documents(client: Client = Depends(get_supabase_client)):
    return list_documents()

@app.delete("/documents/{doc_id}")
async def remove_document(doc_id: str, client: Client = Depends(get_supabase_client)):
    return delete_document(doc_id)
