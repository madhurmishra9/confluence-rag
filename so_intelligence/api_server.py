"""
FastAPI Backend Server for SO Intelligence Dashboard
Provides REST & WebSocket endpoints for dashboard consumption
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import asdict
import traceback

from fastapi import FastAPI, HTTPException, Query, WebSocket, BackgroundTasks, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import uvicorn

from config import AgentConfig
from orchestrator import Orchestrator, RunResult
from cache_manager import CacheManager
from solution_verifier import VerifiedSuggestion
from temporal_comparator import ComparisonResult

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ========================
# Pydantic Models
# ========================

class TagRequest(BaseModel):
    tag: str


class RunRequest(BaseModel):
    tags: Optional[List[str]] = None
    date_range_days: int = 30
    intervention_date: Optional[str] = None
    force_refresh: bool = False


class StatusResponse(BaseModel):
    agent_status: str
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    quota_remaining: int
    ollama_healthy: bool


class TagValidationResponse(BaseModel):
    valid: bool
    suggestion: Optional[str] = None


class RunResponse(BaseModel):
    run_id: str
    status: str


class RunStatusResponse(BaseModel):
    run_id: str
    status: str
    progress_pct: int
    current_step: str
    errors: List[str]


class SuggestionFilterParams(BaseModel):
    tag: Optional[str] = None
    min_confidence: float = 0.0
    verified_only: bool = False


class ReportResponse(BaseModel):
    pdf_url: Optional[str] = None
    docx_url: Optional[str] = None
    generated_at: Optional[str] = None


# ========================
# Global State
# ========================

config = AgentConfig()
orchestrator = Orchestrator(config)
cache_manager = CacheManager(config.db_path)

# Active WebSocket connections for progress streaming
active_connections: List[WebSocket] = []

# Track running tasks
running_tasks: Dict[str, Dict[str, Any]] = {}

# ========================
# FastAPI App Setup
# ========================

app = FastAPI(title="SO Intelligence API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================
# Helper Functions
# ========================

async def broadcast_progress(message: Dict[str, Any]):
    """Broadcast progress message to all connected WebSocket clients"""
    disconnected = []
    for ws in active_connections:
        try:
            await ws.send_json(message)
        except Exception as e:
            logger.warning(f"Error sending to WebSocket: {e}")
            disconnected.append(ws)
    
    # Remove disconnected clients
    for ws in disconnected:
        active_connections.remove(ws)


async def run_orchestrator_task(run_id: str, tags: List[str], date_range_days: int, 
                                 intervention_date: Optional[str], force_refresh: bool):
    """Background task to run orchestrator and stream progress"""
    try:
        running_tasks[run_id]["status"] = "IN_PROGRESS"
        running_tasks[run_id]["progress_pct"] = 0
        running_tasks[run_id]["current_step"] = "Initializing"
        running_tasks[run_id]["errors"] = []

        await broadcast_progress({
            "run_id": run_id,
            "step": "STARTED",
            "status": "IN_PROGRESS",
            "pct": 0,
            "message": "Starting orchestrator run",
            "timestamp": datetime.now().isoformat()
        })

        # Call orchestrator with progress tracking
        result = await asyncio.to_thread(
            orchestrator.run,
            tags or config.default_tags,
            date_range_days,
            intervention_date,
            force_refresh
        )

        running_tasks[run_id]["status"] = result.status
        running_tasks[run_id]["progress_pct"] = 100
        running_tasks[run_id]["current_step"] = "Completed"
        running_tasks[run_id]["result"] = result

        await broadcast_progress({
            "run_id": run_id,
            "step": "COMPLETED",
            "status": result.status,
            "pct": 100,
            "message": f"Run completed with status: {result.status}",
            "timestamp": datetime.now().isoformat()
        })

        # Cache the result
        cache_manager.cache_run_result(run_id, result)

    except Exception as e:
        logger.error(f"Error in orchestrator task {run_id}: {e}\n{traceback.format_exc()}")
        running_tasks[run_id]["status"] = "FAILED"
        running_tasks[run_id]["errors"].append(str(e))

        await broadcast_progress({
            "run_id": run_id,
            "step": "ERROR",
            "status": "FAILED",
            "pct": 0,
            "message": f"Error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


# ========================
# Status Endpoints
# ========================

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get current agent status"""
    last_run = cache_manager.get_latest_run()
    last_run_at = last_run["created_at"] if last_run else None
    
    # Check Ollama health
    ollama_healthy = True
    try:
        # Simple health check - would call Ollama endpoint
        pass
    except:
        ollama_healthy = False

    return StatusResponse(
        agent_status="IDLE" if not running_tasks else "RUNNING",
        last_run_at=last_run_at,
        next_run_at=(datetime.now() + timedelta(hours=1)).isoformat(),
        quota_remaining=9000,  # Placeholder - should fetch from API log
        ollama_healthy=ollama_healthy
    )


# ========================
# Tag Endpoints
# ========================

@app.get("/api/tags")
async def get_tags():
    """Get current tag list from config"""
    return {"tags": config.default_tags}


@app.post("/api/tags", response_model=TagValidationResponse)
async def add_tag(req: TagRequest):
    """Validate and add tag to config"""
    try:
        # Validate tag via SO API (simplified - would call SO API)
        tag = req.tag.lower().strip()
        
        if not tag or len(tag) < 2:
            return TagValidationResponse(valid=False, suggestion="Tag must be at least 2 characters")
        
        if tag in config.default_tags:
            return TagValidationResponse(valid=False, suggestion="Tag already exists")
        
        # In production, validate against SO API
        config.default_tags.append(tag)
        return TagValidationResponse(valid=True)
    
    except Exception as e:
        logger.error(f"Error validating tag: {e}")
        return TagValidationResponse(valid=False, suggestion=f"Validation error: {str(e)}")


@app.delete("/api/tags/{tag}")
async def remove_tag(tag: str):
    """Remove tag from config"""
    if tag in config.default_tags:
        config.default_tags.remove(tag)
        return {"success": True, "tags": config.default_tags}
    raise HTTPException(status_code=404, detail="Tag not found")


# ========================
# Run Management Endpoints
# ========================

@app.get("/api/run/latest")
async def get_latest_run():
    """Get latest RunResult from cache"""
    latest = cache_manager.get_latest_run()
    if not latest:
        raise HTTPException(status_code=404, detail="No runs found")
    
    return latest


@app.post("/api/run", response_model=RunResponse)
async def trigger_run(req: RunRequest, background_tasks: BackgroundTasks):
    """Trigger a new orchestrator run in background"""
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    running_tasks[run_id] = {
        "status": "STARTED",
        "progress_pct": 0,
        "current_step": "Initializing",
        "errors": [],
        "created_at": datetime.now().isoformat()
    }
    
    background_tasks.add_task(
        run_orchestrator_task,
        run_id,
        req.tags,
        req.date_range_days,
        req.intervention_date,
        req.force_refresh
    )
    
    return RunResponse(run_id=run_id, status="STARTED")


@app.get("/api/run/{run_id}/status", response_model=RunStatusResponse)
async def get_run_status(run_id: str):
    """Get status of a specific run"""
    if run_id not in running_tasks:
        raise HTTPException(status_code=404, detail="Run not found")
    
    task = running_tasks[run_id]
    return RunStatusResponse(
        run_id=run_id,
        status=task["status"],
        progress_pct=task["progress_pct"],
        current_step=task["current_step"],
        errors=task.get("errors", [])
    )


# ========================
# Suggestions Endpoints
# ========================

@app.get("/api/suggestions")
async def get_suggestions(
    tag: Optional[str] = Query(None),
    min_confidence: float = Query(0.0),
    verified_only: bool = Query(False)
):
    """Get filtered suggestions list"""
    latest = cache_manager.get_latest_run()
    if not latest or "suggestions" not in latest:
        return {"suggestions": []}
    
    suggestions = latest.get("suggestions", [])
    
    # Filter by tag
    if tag:
        suggestions = [s for s in suggestions if s.get("tag") == tag]
    
    # Filter by confidence
    suggestions = [s for s in suggestions if s.get("confidence_score", 0) >= min_confidence]
    
    # Filter by status
    if verified_only:
        suggestions = [s for s in suggestions if s.get("status") == "VERIFIED"]
    
    return {"suggestions": suggestions}


# ========================
# Comparison Endpoints
# ========================

@app.get("/api/comparison/{tag}")
async def get_comparison(tag: str):
    """Get ComparisonResult for a specific tag"""
    latest = cache_manager.get_latest_run()
    if not latest or "comparisons" not in latest:
        raise HTTPException(status_code=404, detail="No comparisons found")
    
    comparisons = latest.get("comparisons", {})
    if tag not in comparisons:
        raise HTTPException(status_code=404, detail=f"No comparison found for tag: {tag}")
    
    return comparisons[tag]


# ========================
# Report Endpoints
# ========================

@app.get("/api/reports/latest", response_model=ReportResponse)
async def get_latest_reports():
    """Get latest report URLs and metadata"""
    latest = cache_manager.get_latest_run()
    if not latest or "report_paths" not in latest:
        return ReportResponse()
    
    report_paths = latest.get("report_paths", {})
    
    # Construct URLs
    pdf_url = f"/reports/{report_paths.get('pdf', '')}" if report_paths.get('pdf') else None
    docx_url = f"/reports/{report_paths.get('docx', '')}" if report_paths.get('docx') else None
    
    return ReportResponse(
        pdf_url=pdf_url,
        docx_url=docx_url,
        generated_at=latest.get("created_at")
    )


@app.get("/reports/{filename}")
async def serve_report(filename: str):
    """Serve report files from ./reports/ directory"""
    import os
    report_path = os.path.join("reports", filename)
    
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(report_path, media_type="application/octet-stream")


# ========================
# WebSocket Endpoint
# ========================

@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """WebSocket endpoint for real-time progress streaming"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive, receive ping/pong
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


# ========================
# Health Check
# ========================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# ========================
# Root
# ========================

@app.get("/")
async def root():
    """API root"""
    return {
        "title": "SO Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# ========================
# Main
# ========================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
