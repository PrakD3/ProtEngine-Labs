"""LangGraph orchestrator: runs full pipeline, publishes SSE, stores results."""

import asyncio
import os
import time
import uuid
from typing import AsyncIterator

# Load .env variables early
from dotenv import load_dotenv
load_dotenv()

os.environ.setdefault("LANGCHAIN_TRACING_V2", os.getenv("LANGCHAIN_TRACING_V2", "false"))
os.environ.setdefault(
    "LANGCHAIN_ENDPOINT", os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
)
os.environ.setdefault("LANGCHAIN_API_KEY", os.getenv("LANGCHAIN_API_KEY", ""))
os.environ.setdefault(
    "LANGCHAIN_PROJECT", os.getenv("LANGCHAIN_PROJECT", "drug-discovery-hackathon")
)

from pipeline.state import AgentStatus, PipelineMode

# In-memory session store
_sessions: dict[str, dict] = {}
_sse_queues: dict[str, asyncio.Queue] = {}
_active_tasks: dict[str, asyncio.Task] = {} # For mid-run cancellation

AGENT_ORDER = [
    # Stage 1: Data Acquisition
    ("MutationParserAgent", 5),
    ("PlannerAgent", 10),
    ("FetchAgent", 15),
    
    # Stage 2-3: Structure & Variant Analysis
    ("StructurePrepAgent", 25),
    ("VariantEffectAgent", 30),
    ("PocketDetectionAgent", 35),
    
    # Stage 4-5: Molecule Design & Docking
    ("MoleculeGenerationAgent", 45),
    ("DockingAgent", 55),
    ("SelectivityAgent", 62),
    ("ADMETAgent", 68),
    ("LeadOptimizationAgent", 74),
    
    # Stage 6-7: Ranking & Validation
    ("GNNAffinityAgent", 80),
    ("MDValidationAgent", 90),
    ("ResistanceAgent", 92),
    
    # Stage 8-9: Context Analysis
    ("SimilaritySearchAgent", 94),
    ("SynergyAgent", 96),
    ("ClinicalTrialAgent", 97),
    
    # Stage 10: Output
    ("SynthesisAgent", 98),
    ("KnowledgeGraphAgent", 98.5),
    ("ExplainabilityAgent", 99),
    ("ReportAgent", 100),
]


def _import_agent(name: str):
    mod = __import__(f"agents.{name}", fromlist=[name])
    cls = getattr(mod, name)
    return cls()


class OrchestratorAgent:
    """Runs the full 19-agent V4 pipeline sequentially with SSE events."""

    async def run_pipeline(self, query: str, session_id: str, mode: str = "full") -> dict:
        from utils.logger import get_logger
        log = get_logger("orchestrator")
        log.info(f"Starting pipeline for session {session_id}: {query}")
        
        # Store currently running task
        current_task = asyncio.current_task()
        if current_task:
            _active_tasks[session_id] = current_task
            
        start = time.time()
        
        try:
            # Get existing session if it was pre-initialized, or create new one
            state = _sessions.get(session_id)
            if state is None:
                state = {}

            state["query"] = query
            state["session_id"] = session_id
            state["mode"] = PipelineMode.FULL if mode == "full" else PipelineMode.LITE
            state.setdefault("agent_statuses", {})
            state.setdefault("errors", [])
            state.setdefault("warnings", [])
            state.setdefault("confidence_scores", {})
            state.setdefault("langsmith_run_id", None)
            state.setdefault("execution_time_ms", 0)
            state.setdefault("llm_provider_used", "unknown")
            state.setdefault("cancelled", False)

            _sessions[session_id] = state

            queue = _sse_queues.get(session_id)
            if queue is None:
                queue = asyncio.Queue()
                _sse_queues[session_id] = queue

            agent_names = [a[0] for a in AGENT_ORDER]
            for name in agent_names:
                state["agent_statuses"].setdefault(name, AgentStatus.PENDING)

            await queue.put({"event": "pipeline_start", "session_id": session_id, "query": query})

            for agent_name, progress in AGENT_ORDER:
                if state.get("cancelled"):
                    break
                    
                state["agent_statuses"][agent_name] = AgentStatus.RUNNING
                _sessions[session_id] = state
                await queue.put({"event": "agent_start", "agent": agent_name, "progress": progress - 5})

                try:
                    agent = _import_agent(agent_name)
                    # Use Shield to prevent cancellation mid-agent during sensitive IO? 
                    # Actually, we want to allow cancellation even mid-agent.
                    result = await agent.run(state)
                    state.update(result)
                    state["agent_statuses"][agent_name] = AgentStatus.COMPLETE
                    _sessions[session_id] = state
                    await queue.put(
                        {
                            "event": "agent_complete",
                            "agent": agent_name,
                            "progress": progress,
                            "data": {k: v for k, v in result.items() if k != "errors"},
                        }
                    )
                except asyncio.CancelledError:
                    log.info(f"Task for session {session_id} was explicitly cancelled mid-agent.")
                    state["cancelled"] = True
                    raise
                except Exception as exc:
                    state["agent_statuses"][agent_name] = AgentStatus.FAILED
                    state.setdefault("errors", []).append(f"{agent_name}: {exc}")
                    _sessions[session_id] = state
                    await queue.put({"event": "agent_error", "agent": agent_name, "error": str(exc)})

        except asyncio.CancelledError:
            # Handle the cleanup of skipped agents
            agent_names = [a[0] for a in AGENT_ORDER]
            for pending_name in agent_names:
                if state["agent_statuses"].get(pending_name) in [AgentStatus.PENDING, AgentStatus.RUNNING]:
                    if state["agent_statuses"].get(pending_name) == AgentStatus.RUNNING:
                        state["agent_statuses"][pending_name] = AgentStatus.FAILED
                    else:
                        state["agent_statuses"][pending_name] = AgentStatus.SKIPPED
            
            state["status"] = "cancelled"
            state["cancelled"] = True
            _sessions[session_id] = state
            
            queue = _sse_queues.get(session_id)
            if queue:
                await queue.put(
                    {
                        "event": "pipeline_cancelled",
                        "data": {
                            "cancelled": True,
                            "status": "cancelled",
                            "agent_statuses": state.get("agent_statuses", {}),
                        },
                    }
                )
            log.info(f"Pipeline cleanup complete for session {session_id}")
        finally:
            # Re-confirm state and remove task
            if session_id in _active_tasks:
                del _active_tasks[session_id]

        state["execution_time_ms"] = int((time.time() - start) * 1000)
        
        # Don't auto-save if cancelled
        if not state.get("cancelled") and os.getenv("AUTO_SAVE_DISCOVERIES", "").lower() == "true":
            try:
                from utils.db import save_discovery
                await save_discovery(state)
            except Exception as e:
                log.error(f"AUTO_SAVE failed for session {session_id}: {e}")

        _sessions[session_id] = state
        
        # Final event (if not cancelled by now)
        if not state.get("cancelled"):
            state["status"] = "complete"
            await queue.put(
                {
                    "event": "pipeline_complete",
                    "data": state,
                }
            )
        return state

    def get_session(self, session_id: str) -> dict | None:
        return _sessions.get(session_id)

    async def stream_events(self, session_id: str) -> AsyncIterator[dict]:
        queue = _sse_queues.get(session_id)
        if not queue:
            return
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=120)
                yield event
                if event.get("event") in ["pipeline_complete", "pipeline_cancelled"]:
                    break
            except asyncio.TimeoutError:
                break
