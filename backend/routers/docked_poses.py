"""GET /api/docked-poses/{session_id}/{pose_id} — docked ligand pose file."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/docked-poses/{session_id}/{pose_id}")
async def get_docked_pose(session_id: str, pose_id: str):
    from agents.OrchestratorAgent import _sessions

    docked_root = (Path(__file__).parent.parent / "data" / "docked_poses").resolve()

    pose_path = None
    state = _sessions.get(session_id)
    if state:
        pose_map = state.get("docked_pose_map", {})
        pose_path = pose_map.get(pose_id)

    from utils.db import get_session_by_session_id
    from fastapi import Response

    path = None
    if pose_path:
        path = Path(pose_path)
    else:
        # Fallback to filesystem
        base = docked_root / session_id
        candidate_pdb = base / f"{pose_id}.pdb"
        candidate_pdbqt = base / f"{pose_id}.pdbqt"
        if candidate_pdb.exists():
            path = candidate_pdb
        elif candidate_pdbqt.exists():
            path = candidate_pdbqt

    if path and path.exists():
        media_type = "chemical/x-pdb" if path.suffix.lower() == ".pdb" else "chemical/x-pdbqt"
        return FileResponse(path, media_type=media_type, filename=path.name)

    # 3. Fallback to Database content
    db_state = await get_session_by_session_id(session_id)
    if db_state:
        results = db_state.get("docking_results", [])
        for r in results:
            if r.get("pose_id") == pose_id:
                content = r.get("pose_content")
                if content:
                    return Response(content, media_type="chemical/x-pdb")

    raise HTTPException(status_code=404, detail="Docked pose not found in FS or DB")
