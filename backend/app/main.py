import os
import shutil
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Import core logic from services layout
from app.services.vector_store import process_pdf, get_vector_store
from app.services.agent import agent_builder
from app.services.database import get_db_pool
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 [FastAPI Engine Start] Taking over the Postgres long-lived connection...")
    pool = get_db_pool()
    await pool.open()
    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()
    
    # Dynamically bind the stateful agent to the FastAPI context
    app.state.agent_app = agent_builder.compile(checkpointer=checkpointer)
    yield
    print("🛑 [FastAPI Engine Stop] Releasing Postgres DB resources...")
    await pool.close()

app = FastAPI(title="Risk Auditor AI - Clean Architecture", lifespan=lifespan)

# CORS configuration for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routing Endpoints ---

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        file_path = os.path.join(data_dir, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Delegate document processing to the service layer
        process_pdf(file_path)
        return {"status": "success", "message": f"Document '{file.filename}' processed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ChatInput(BaseModel):
    message: str
    user_id: str

@app.post("/chat")
async def chat(request: Request, data: ChatInput):
    # Retrieve the mounted AI engine from app state
    agent_app = request.app.state.agent_app
    
    try:
        # Use user_id as thread_id to persist and track conversational context
        config = {"configurable": {"thread_id": data.user_id}}
        result = await agent_app.ainvoke({"messages": [HumanMessage(content=data.message)]}, config=config)
        return {"answer": result["messages"][-1].content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Passing the import string 'main:app' allows uvicorn worker to hot-reload successfully
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)