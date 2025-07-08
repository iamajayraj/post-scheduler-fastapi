# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Any, Optional
import uvicorn

# import your graph‐building functions
from main import build_generate_graph, build_feedback_graph
from fastapi.middleware.cors import CORSMiddleware


# 1. Define a Pydantic model mirroring your TypedDict
class PostState(BaseModel):
    id: int
    date: str
    time: str
    topic: str
    context: str
    tone: str
    cta: str
    status: Optional[str] = None
    output_post: Optional[str] = None
    feedback: Optional[str] = None
    approved: Optional[bool] = None
    messages: Optional[List[Any]] = None

# 2. Create FastAPI app and compile graphs once at startup
app = FastAPI(title="LangGraph as FastAPI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to your deployed frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

generate_graph = build_generate_graph()
feedback_graph = build_feedback_graph()

@app.get("/")
async def home():
    return "API Working Fine"

# 3. Expose /generate
@app.post("/generate", response_model=PostState)
async def generate_post(state: PostState):
    try:
        result = generate_graph.invoke(state.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Expose /feedback
@app.post("/feedback", response_model=PostState)
async def refine_and_schedule(state: PostState):
    try:
        result = feedback_graph.invoke(state.model_dump())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. Run with: uvicorn app:app --reload
if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.getenv("PORT", 8000))  
    uvicorn.run("server:app", host=host, port=port, reload=True)
