"""POST /api/analyze — start a pipeline run."""

import asyncio

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
import agents.OrchestratorAgent  # Import module, not variable

router = APIRouter()


class AnalysisRequest(BaseModel):
    query: str
    mode: str = "full"


@router.post("/analyze")
async def analyze(req: AnalysisRequest, background_tasks: BackgroundTasks):
    import uuid
    from pipeline.graph import get_orchestrator

    session_id = str(uuid.uuid4())
    
    # Initialize session immediately so save endpoint doesn't get 404
    # Access _sessions dynamically to handle module reloads
    agents.OrchestratorAgent._sessions[session_id] = {
        "query": req.query,
        "session_id": session_id,
        "mode": req.mode,
        "status": "initializing",
    }
    
    orchestrator = get_orchestrator()
    background_tasks.add_task(orchestrator.run_pipeline, req.query, session_id, req.mode)
    return {"session_id": session_id, "status": "started", "query": req.query}
