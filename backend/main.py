import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Clean up old DB on restart
db_path = "./chroma_db"
if os.path.exists(db_path):
    try:
        shutil.rmtree(db_path)
        print(f"Deleted old database at {db_path}")
    except Exception as e:
        print(f"Warning: Could not delete old database: {e}")

from .agents.coordinator import coordinator
from .mcp.broker import broker

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up Agentic RAG Chatbot...")
    yield
    # Shutdown
    print("Shutting down...")

from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Agentic RAG Chatbot", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Frontend
# We mount it at /app or similar, but for SPA feel let's mount root to static
# But we have @app.get("/") already. Let's move API root or checking priority.
# Fastapi matches in order.
# Let's Serve static files on root, but exclude API specific paths effectively by order.
# Actually, better to serve "/" as FileResponse('frontend/index.html') and mount /static for assets.
# But for simplicity, let's mount / to StaticFiles with html=True
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    context: str
    trace_id: str

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file filename")
    
    # Save to temp file
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        
    try:
        # Pass to Coordinator
        result = await coordinator.handle_file_upload(tmp_path, file.filename)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp file? 
        # For IngestionAgent that uses open() it might be okay.
        # But if we delete it too fast, Ingestion might fail if it's async and delayed.
        # Coordinator.handle_file_upload waits for IngestionAgent, so it is safe to delete here.
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = await coordinator.handle_user_query(request.query)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return ChatResponse(
        answer=result.get("answer", ""),
        context=result.get("context", ""),
        trace_id=result.get("trace_id", "")
    )
