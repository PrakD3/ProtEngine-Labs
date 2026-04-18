"""POST /api/analyze — start a pipeline run."""

import asyncio

from fastapi import APIRouter, BackgroundTasks, HTTPException
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
        "cancelled": False,
    }
    
    orchestrator = get_orchestrator()
    background_tasks.add_task(orchestrator.run_pipeline, req.query, session_id, req.mode)
    return {"session_id": session_id, "status": "started", "query": req.query}


@router.post("/cancel/{session_id}")
async def cancel(session_id: str):
    from agents.OrchestratorAgent import _sessions, _sse_queues

    state = _sessions.get(session_id)
    if not state:
        return {"session_id": session_id, "status": "not_found"}
    if state.get("final_report"):
        return {"session_id": session_id, "status": "complete"}

    state["cancelled"] = True
    state["status"] = "cancelled"

    queue = _sse_queues.get(session_id)
    if queue:
        await queue.put(
            {"event": "pipeline_cancelled", "data": {"cancelled": True, "status": "cancelled"}}
        )

    return {"session_id": session_id, "status": "cancelled"}
