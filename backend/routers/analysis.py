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
    from agents.OrchestratorAgent import _sessions, _sse_queues, _active_tasks

    state = _sessions.get(session_id)
    if not state:
        return {"session_id": session_id, "status": "not_found"}
    
    if state.get("final_report") or state.get("status") == "complete":
        return {"session_id": session_id, "status": "already_complete"}

    state["cancelled"] = True
    state["status"] = "cancelled"

    # Immediately cancel the running asyncio task
    task = _active_tasks.get(session_id)
    if task and not task.done():
        task.cancel()
        return {"session_id": session_id, "status": "cancellation_requested"}

    # Fallback: if task isn't in registry but queue is alive
    queue = _sse_queues.get(session_id)
    if queue:
        await queue.put(
            {"event": "pipeline_cancelled", "data": {"cancelled": True, "status": "cancelled"}}
        )

    return {"session_id": session_id, "status": "cancelled"}
