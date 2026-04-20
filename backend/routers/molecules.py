"""GET /api/molecules/{session_id}."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/molecules/{session_id}")
async def get_molecules(session_id: str):
    import agents.OrchestratorAgent  # Import module, not variable

    if session_id == "demo-egfr":
        return {
            "session_id": "demo-egfr",
            "query": "EGFR T790M",
            "status": "complete",
            "final_report": {
                "summary": "High-affinity lead compound identified for EGFR T790M resistance mutation. Lead-1 shows strong binding (-9.2 kcal/mol) and ideal ADMET profile.",
                "ranked_leads": [
                    {
                        "rank": 1,
                        "compound_name": "PEL-790-X1",
                        "smiles": "CC1=CC(=C(C=C1)NC2=NC=C(C(=N2)NC3=CC=CC(=C3)S(=O)(=O)C)C)OC",
                        "binding_energy": -9.2,
                        "sa_score": 2.4,
                        "synthesis_cost": 1250,
                        "synthesis_steps": 4
                    }
                ],
                "metrics": {"execution_time_ms": 42500}
            },
            "agent_statuses": {a: "complete" for a in ["MutationParser", "Planner", "Fetch", "StructurePrep", "Docking", "Report"]},
            "pdb_content": "HEADER    PROTEIN DATA BANK DUMMY CONTENT\nATOM      1  N   ALA A   1      20.123  30.456  40.789  1.00 95.00           N",
            "confidence_banner": {"tier": "WELL_KNOWN", "plddt": 96.5}
        }

    state = agents.OrchestratorAgent._sessions.get(session_id)

    # Not in memory (backend restarted) — try recovering from Neon
    if not state:
        try:
            from utils.db import get_session_by_session_id
            state = await get_session_by_session_id(session_id)
        except Exception:
            state = None

    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    # Bump this discovery to the top of the history list
    from utils.db import bump_discovery
    await bump_discovery(session_id)

    return {
        "session_id": session_id,
        "query": state.get("query"),
        "mutation_context": state.get("mutation_context"),
        "literature": state.get("literature", []),
        "structures": state.get("structures", []),
        "pdb_content": state.get("pdb_content", ""),
        "binding_pocket": state.get("binding_pocket"),
        "pocket_detection_method": state.get("pocket_detection_method"),
        "pocket_delta": state.get("pocket_delta"),
        "generated_molecules": state.get("generated_molecules", []),
        "docking_results": state.get("docking_results", []),
        "selectivity_results": state.get("selectivity_results", []),
        "admet_profiles": state.get("admet_profiles", []),
        "toxicophore_highlights": state.get("toxicophore_highlights", []),
        "optimized_leads": state.get("optimized_leads", []),
        "evolution_tree": state.get("evolution_tree"),
        "similar_compounds": state.get("similar_compounds", []),
        "synergy_predictions": state.get("synergy_predictions", []),
        "clinical_trials": state.get("clinical_trials", []),
        "knowledge_graph": state.get("knowledge_graph"),
        "reasoning_trace": state.get("reasoning_trace"),
        "summary": state.get("summary"),
        "resistance_flags": state.get("resistance_flags", []),
        "resistance_forecast": state.get("resistance_forecast"),
        "resistant_drugs": state.get("resistant_drugs", []),
        "recommended_drugs": state.get("recommended_drugs", []),
        "md_results": state.get("md_results", []),
        "sa_scores": state.get("sa_scores", []),
        "synthesis_routes": state.get("synthesis_routes", []),
        "confidence": state.get("confidence"),
        "confidence_banner": state.get("confidence_banner"),
        "esm1v_score": state.get("esm1v_score"),
        "esm1v_confidence": state.get("esm1v_confidence"),
        "final_report": state.get("final_report"),
        "status": state.get("status"),
        "cancelled": state.get("cancelled", False),
        "agent_statuses": state.get("agent_statuses", {}),
        "execution_time_ms": state.get("execution_time_ms", 0),
        "langsmith_run_id": state.get("langsmith_run_id"),
        "llm_provider_used": state.get("llm_provider_used", "unknown"),
        "discovery_id": state.get("discovery_id"),
    }
