"""GET /api/structure/{session_id} — receptor structure for a session."""

from fastapi import APIRouter, HTTPException, Response

router = APIRouter()


@router.get("/structure/{session_id}")
async def get_structure(session_id: str):
    from agents.OrchestratorAgent import _sessions
    from utils.db import get_session_by_session_id

    # 1. Try Memory
    state = _sessions.get(session_id)
    pdb_content = state.get("pdb_content") if state else None

    # 2. Try Database
    if not pdb_content:
        db_state = await get_session_by_session_id(session_id)
        if db_state:
            pdb_content = db_state.get("pdb_content")

    if not pdb_content:
        raise HTTPException(status_code=404, detail="Structure not available")

    return Response(pdb_content, media_type="chemical/x-pdb")
