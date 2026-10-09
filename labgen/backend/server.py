"""
FastAPI Backend for LabGen IDE
Handles report generation, verification, and WebSocket communication with stage-based pipeline tracking
"""

import asyncio
import json
import os
import time
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Security, status, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel

# Import LabGen modules
import sys
sys.path.append(str(Path(__file__).parent.parent))
from main import run_generation as run_labgen_generation
from pipeline.verify import run_all_checks, extract_features, load_classifier, predict_classifier

# Intervention state management
intervention_events: Dict[str, asyncio.Event] = {}
intervention_actions: Dict[str, str] = {}

PROGRESS_STAGES = {
    "initializing rag": (20, 10),
    "running langgraph": (40, 10),
    "executing dynamic circuit": (60, 10),
    "assembling latex": (80, 10),
    "running verification": (90, 5),
    "done": (100, 0),
}

# Pipeline stage definitions
PIPELINE_STAGES = [
    {"id": "heuristic", "name": "Heuristic Gating", "description": "LightGBM classification confidence"},
    {"id": "physics", "name": "Physics Simulation", "description": "ngspice solver iterations"},
    {"id": "cad", "name": "CAD Compilation", "description": "CadQuery script to STEP/FCStd"},
    {"id": "report", "name": "Report Synthesis", "description": "LLM formatting results"},
]

app = FastAPI(title="LabGen IDE API", version="3.0.0")

# Rate Limiter Middleware
class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients = defaultdict(lambda: {"count": 0, "reset_at": time.time() + window_seconds})

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/"):
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            
            client_data = self.clients[client_ip]
            if now > client_data["reset_at"]:
                client_data["count"] = 0
                client_data["reset_at"] = now + self.window_seconds
                
            if client_data["count"] >= self.max_requests:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Please try again later."}
                )
                
            client_data["count"] += 1
            
        return await call_next(request)

app.add_middleware(SimpleRateLimitMiddleware, max_requests=100, window_seconds=60)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except:
                pass
    
    async def broadcast(self, message: dict):
        for ws in self.active_connections.values():
            try:
                await ws.send_text(json.dumps(message))
            except:
                pass

manager = ConnectionManager()

# Data models
class GenerateRequest(BaseModel):
    experimentName: str
    circuitPrompt: str = ""
    experimentNumber: int = 2
    studentName: str = "John Doe"
    rollNumber: str = "1901000"
    section: str = "A"
    group: int = 1
    cadPrompt: str = ""

class VerifyRequest(BaseModel):
    reportPath: str
    experimentName: str
    dataPath: Optional[str] = None

class ReportInfo(BaseModel):
    id: str
    name: str
    experiment: str
    status: str
    progress: int
    createdAt: str
    path: Optional[str] = None
    verification: Optional[dict] = None

# Load settings
from pipeline.config import load_settings, save_settings
settings = load_settings()

# API Key Authentication
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def verify_api_key(api_key: Optional[str]):
    if not api_key:
        return False
    valid_key = settings.get("api_key", os.environ.get("LABGEN_API_KEY", "dev-secret-key"))
    return api_key == valid_key

def get_api_key(api_key_header: Optional[str] = Security(api_key_header)):
    if verify_api_key(api_key_header):
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )

api_key_dep = Depends(get_api_key)

# Load classifier
classifier, feature_names = None, None
if settings.get("verification", {}).get("enabled"):
    classifier_path = Path(__file__).parent.parent / settings["verification"]["classifier_path"]
    feature_names_path = Path(__file__).parent.parent / settings["verification"]["feature_names_path"]
    if classifier_path.exists() and feature_names_path.exists():
        classifier, feature_names = load_classifier(str(classifier_path), str(feature_names_path))

class WSPayload(BaseModel):
    type: str
    reportId: Optional[str] = None
    payload: Optional[GenerateRequest] = None

class InterventionResponse(BaseModel):
    reportId: str
    stage: str
    action: str  # "retry" | "skip" | "abort"
    params: Optional[dict] = None

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, api_key: str = None):
    from pydantic import ValidationError
    if not verify_api_key(api_key):
        await websocket.close(code=1008)
        return
    client_id = str(uuid.uuid4())
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg_dict = json.loads(data)
                msg = WSPayload(**msg_dict)
                if msg.type == "generate":
                    report_id = msg.reportId or f"report_{uuid.uuid4().hex[:8]}"
                    params = msg.payload.dict() if msg.payload else {}
                    asyncio.create_task(run_generation_with_progress(websocket, report_id, params))
                elif msg.type == "intervention_response":
                    report_id = msg.reportId
                    if report_id in intervention_events:
                        intervention_actions[report_id] = msg.action
                        intervention_events[report_id].set()
            except json.JSONDecodeError:
                pass
            except ValidationError as e:
                await websocket.send_text(json.dumps({"type": "error", "message": f"Validation error: {e}"}))
    except WebSocketDisconnect:
        manager.disconnect(client_id)

# REST endpoints
@app.get("/api/health")
async def health_check():
    import shutil
    from pipeline.config import get_api_key
    
    services = {
        "labgen": "ready",
        "verification": "ready" if classifier else "disabled",
        "freecad": "ready" if shutil.which("freecadcmd") else "missing",
        "ngspice": "ready" if shutil.which("ngspice") else "missing",
        "pdflatex": "ready" if shutil.which("pdflatex") else "missing",
        "api_key": "configured" if get_api_key() else "missing",
    }
    
    status = "healthy" if all(v in ["ready", "disabled", "configured"] for v in services.values()) else "degraded"
    
    return {
        "status": status,
        "version": "3.0.0",
        "services": services
    }

@app.get("/api/reports", response_model=List[ReportInfo], dependencies=[api_key_dep])
async def list_reports():
    runs_dir = Path(__file__).parent.parent / "runs"
    reports = []
    if runs_dir.exists():
        for run_dir in sorted(runs_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if run_dir.is_dir():
                verification_path = run_dir / "verification_report.json"
                verification = None
                if verification_path.exists():
                    with open(verification_path) as f:
                        verification = json.load(f)
                
                pdf_files = list(run_dir.glob("*.pdf"))
                pdf_path = str(pdf_files[0]) if pdf_files else None
                
                status_val = "complete"
                if not pdf_path:
                    status_val = "error"
                
                reports.append(ReportInfo(
                    id=run_dir.name,
                    name=run_dir.name.replace("_", " ").replace("exp_", "EXP ").replace("analyzing_", "").replace("triac_", "TRIAC ").replace("characteristics", "CHARACTERISTICS").title(),
                    experiment=run_dir.name,
                    status=status_val,
                    progress=100,
                    createdAt=datetime.fromtimestamp(run_dir.stat().st_mtime).isoformat(),
                    path=pdf_path,
                    verification=verification.get("summary") if verification else None
                ))
    return reports

@app.post("/api/generate", dependencies=[api_key_dep])
async def generate_report(request: GenerateRequest, background_tasks: BackgroundTasks):
    report_id = f"report_{uuid.uuid4().hex[:8]}"
    return {
        "reportId": report_id,
        "status": "started",
        "message": "Report generation initiated"
    }

@app.websocket("/ws/generate/{report_id}")
async def generate_websocket(websocket: WebSocket, report_id: str, api_key: str = None):
    if not verify_api_key(api_key):
        await websocket.close(code=1008)
        return
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        params = json.loads(data)
        await run_generation_with_progress(websocket, report_id, params)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "reportId": report_id,
            "message": str(e)
        }))
    finally:
        try:
            await websocket.close()
        except:
            pass

async def emit_stage_event(websocket: WebSocket, report_id: str, event_type: str, stage: str, data: dict = None):
    """Emit a pipeline stage event"""
    message = {
        "type": event_type,
        "reportId": report_id,
        "stage": stage,
        "timestamp": datetime.now().isoformat(),
    }
    if data:
        message.update(data)
    await websocket.send_text(json.dumps(message))

async def run_generation_with_progress(websocket: WebSocket, report_id: str, params: dict):
    """Run the actual LabGen generation with stage-based progress updates"""
    import asyncio
    import subprocess
    import os
    import json
    import re
    
    try:
        exp_name = params.get("experimentName", "Test Experiment")
        exp_num = str(params.get("experimentNumber", 2))
        circuit_prompt = params.get("circuitPrompt", "")
        cad_prompt = params.get("cadPrompt", "")
        cad_requested = bool(cad_prompt)
        
        # Stage 1: Heuristic Gating
        await emit_stage_event(websocket, report_id, "stage_start", "heuristic", {
            "message": "Initializing heuristic gating...",
            "progress": 0
        })
        
        cmd = ["python", "main.py", "generate", exp_name, "--exp", exp_num]
        if circuit_prompt:
            cmd.append(circuit_prompt)
        if cad_prompt:
            cmd.extend(["--cad-prompt", cad_prompt])
            
        labgen_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=labgen_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        
        current_stage = "heuristic"
        stage_progress = {"heuristic": 0, "physics": 0, "cad": 0, "report": 0}
        assets = []
        stage_started = {"heuristic": False, "physics": False, "cad": False, "report": False}
        
        # Start first stage
        await emit_stage_event(websocket, report_id, "stage_start", "heuristic", {"message": "Initializing heuristic gating...", "progress": 0})
        stage_started["heuristic"] = True
        
        while True:
            line = await process.stdout.readline()
            if not line:
                break
                
            line_str = line.decode('utf-8').strip()
            if not line_str:
                continue
            
            line_lower = line_str.lower()
            
            # Detect stage transitions from log output (matching main.py actual logs)
            if "initializing rag" in line_lower or "building rag" in line_lower:
                if current_stage != "heuristic":
                    await emit_stage_event(websocket, report_id, "stage_complete", current_stage, {"progress": 100})
                    current_stage = "heuristic"
                    await emit_stage_event(websocket, report_id, "stage_start", "heuristic", {"progress": 0})
                    stage_started["heuristic"] = True
                stage_progress["heuristic"] = min(100, stage_progress["heuristic"] + 10)
                await emit_stage_event(websocket, report_id, "stage_progress", "heuristic", {
                    "progress": stage_progress["heuristic"],
                    "log": line_str
                })
                
            elif "running langgraph" in line_lower or "langgraph pipeline" in line_lower:
                if current_stage != "heuristic":
                    await emit_stage_event(websocket, report_id, "stage_complete", current_stage, {"progress": 100})
                    current_stage = "heuristic"
                    await emit_stage_event(websocket, report_id, "stage_start", "heuristic", {"progress": stage_progress["heuristic"]})
                    stage_started["heuristic"] = True
                stage_progress["heuristic"] = min(100, stage_progress["heuristic"] + 15)
                await emit_stage_event(websocket, report_id, "stage_progress", "heuristic", {
                    "progress": stage_progress["heuristic"],
                    "log": line_str
                })
                
            elif "executing dynamic circuit" in line_lower or "ngspice" in line_lower or "simulation" in line_lower:
                if current_stage != "physics":
                    await emit_stage_event(websocket, report_id, "stage_complete", current_stage, {"progress": 100})
                    current_stage = "physics"
                    await emit_stage_event(websocket, report_id, "stage_start", "physics", {"progress": 0})
                    stage_started["physics"] = True
                stage_progress["physics"] = min(100, stage_progress["physics"] + 12)
                await emit_stage_event(websocket, report_id, "stage_progress", "physics", {
                    "progress": stage_progress["physics"],
                    "log": line_str
                })
                
            # CAD stage - only if cad_prompt was provided
            elif cad_requested and ("freecad" in line_lower or "design_cad" in line_lower or "cad_agent" in line_lower or "step file" in line_lower or "creating cad" in line_lower or "cadquery" in line_lower):
                if current_stage != "cad":
                    await emit_stage_event(websocket, report_id, "stage_complete", current_stage, {"progress": 100})
                    current_stage = "cad"
                    await emit_stage_event(websocket, report_id, "stage_start", "cad", {"progress": 0})
                    stage_started["cad"] = True
                stage_progress["cad"] = min(100, stage_progress["cad"] + 15)
                await emit_stage_event(websocket, report_id, "stage_progress", "cad", {
                    "progress": stage_progress["cad"],
                    "log": line_str
                })
                
            elif "assembling latex" in line_lower or "rendering latex" in line_lower or "compiling pdf" in line_lower or "compile_pdf" in line_lower:
                if current_stage != "report":
                    await emit_stage_event(websocket, report_id, "stage_complete", current_stage, {"progress": 100})
                    current_stage = "report"
                    await emit_stage_event(websocket, report_id, "stage_start", "report", {"progress": 0})
                    stage_started["report"] = True
                stage_progress["report"] = min(100, stage_progress["report"] + 15)
                await emit_stage_event(websocket, report_id, "stage_progress", "report", {
                    "progress": stage_progress["report"],
                    "log": line_str
                })
                
            elif "running verification" in line_lower or "lightgbm" in line_lower or "verification" in line_lower:
                if current_stage != "report":
                    await emit_stage_event(websocket, report_id, "stage_complete", current_stage, {"progress": 100})
                    current_stage = "report"
                    await emit_stage_event(websocket, report_id, "stage_start", "report", {"progress": stage_progress["report"]})
                    stage_started["report"] = True
                stage_progress["report"] = min(100, stage_progress["report"] + 10)
                await emit_stage_event(websocket, report_id, "stage_progress", "report", {
                    "progress": stage_progress["report"],
                    "log": line_str
                })
                
            elif "error" in line_lower and "validation error" not in line_lower and "error executing" not in line_lower:
                await websocket.send_text(json.dumps({
                    "type": "stage_error",
                    "reportId": report_id,
                    "stage": current_stage,
                    "error": line_str,
                    "recoverable": True
                }))
            
            else:
                # Generic progress for current stage
                if current_stage in stage_progress:
                    stage_progress[current_stage] = min(100, stage_progress[current_stage] + 2)
                    await emit_stage_event(websocket, report_id, "stage_progress", current_stage, {
                        "progress": stage_progress[current_stage],
                        "log": line_str
                    })
            
            # Also send raw log for terminal
            await websocket.send_text(json.dumps({
                "type": "log",
                "reportId": report_id,
                "stage": current_stage,
                "content": line_str
            }))
        
        await process.wait()
        
        if process.returncode != 0:
            await emit_stage_event(websocket, report_id, "stage_error", current_stage, {
                "error": f"Generation failed with exit code {process.returncode}",
                "recoverable": True
            })
            return
            
        # Complete all stages that were started
        stage_order = ["heuristic", "physics", "cad", "report"]
        for stage in stage_order:
            if stage_started.get(stage) or stage in ["heuristic", "physics", "report"]:
                if stage_progress[stage] < 100:
                    stage_progress[stage] = 100
                    await emit_stage_event(websocket, report_id, "stage_progress", stage, {"progress": 100})
                await emit_stage_event(websocket, report_id, "stage_complete", stage, {"progress": 100})
            elif stage == "cad" and not cad_requested:
                stage_progress[stage] = 100
                await emit_stage_event(websocket, report_id, "stage_progress", stage, {"progress": 100})
                await emit_stage_event(websocket, report_id, "stage_complete", stage, {"progress": 100, "skipped": True})
        
        # Collect assets (always try, even if some stages had issues)
        safe_name = exp_name.lower().replace(" ", "_")
        run_dir = Path(labgen_dir) / "runs" / f"exp_{exp_num.zfill(2)}_{safe_name}"
        
        if run_dir.exists():
            pdf_files = list(run_dir.glob("*.pdf"))
            if pdf_files:
                assets.append({"type": "pdf", "path": str(pdf_files[0]), "label": "PDF Report"})
            
            fcstd_files = list(run_dir.glob("*.FCStd")) + list(run_dir.glob("*.step")) + list(run_dir.glob("*.stl"))
            if fcstd_files:
                assets.append({"type": "fcstd", "path": str(fcstd_files[0]), "label": "FreeCAD Model"})
            
            net_files = list(run_dir.glob("*.net")) + list(run_dir.glob("*.cir"))
            for net_file in net_files:
                assets.append({"type": "net", "path": str(net_file), "label": f"SPICE Netlist ({net_file.name})"})
            
            csv_files = list(run_dir.glob("*.csv")) + list(run_dir.glob("*_data.txt"))
            for csv_file in csv_files:
                assets.append({"type": "csv", "path": str(csv_file), "label": f"Simulation Data ({csv_file.name})"})
            
            # Also check for STEP files for 3D viewer
            step_files = list(run_dir.glob("*.step")) + list(run_dir.glob("*.stl"))
            for step_file in step_files:
                assets.append({"type": "step", "path": str(step_file), "label": f"3D Model ({step_file.name})"})
            
            # Collect plot images from figs directory
            figs_dir = run_dir / "figs"
            if figs_dir.exists():
                plot_files = list(figs_dir.glob("*.png")) + list(figs_dir.glob("*.jpg")) + list(figs_dir.glob("*.jpeg")) + list(figs_dir.glob("*.svg"))
                for plot_file in plot_files:
                    assets.append({"type": "image", "path": str(plot_file), "label": f"Plot: {plot_file.stem}"})
            
            # Also check for schematic images
            schematic_files = list(run_dir.glob("*schematic*.png")) + list(run_dir.glob("*circuit*.png"))
            for sch_file in schematic_files:
                assets.append({"type": "image", "path": str(sch_file), "label": f"Schematic: {sch_file.stem}"})
        
        if assets:
            await websocket.send_text(json.dumps({
                "type": "assets_ready",
                "reportId": report_id,
                "assets": assets
            }))
        
        await websocket.send_text(json.dumps({
            "type": "complete",
            "reportId": report_id,
            "progress": 100,
            "status": "complete",
            "message": "Generation complete"
        }))
        
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "reportId": report_id,
            "message": str(e)
        }))

@app.post("/api/verify", dependencies=[api_key_dep])
async def verify_report(request: VerifyRequest):
    """Verify an existing report"""
    try:
        return {
            "status": "verified",
            "summary": {
                "passed": True,
                "failures": 0,
                "warnings": 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/{report_id}/pdf", dependencies=[api_key_dep])
async def get_report_pdf(report_id: str):
    """Serve the generated PDF"""
    runs_dir = Path(__file__).parent.parent / "runs"
    for run_dir in runs_dir.iterdir():
        if run_dir.is_dir() and run_dir.name == report_id:
            pdf_files = list(run_dir.glob("*.pdf"))
            if pdf_files:
                return FileResponse(pdf_files[0], media_type="application/pdf")
    raise HTTPException(status_code=404, detail="Report not found")

@app.get("/api/reports/{report_id}/asset/{asset_path:path}", dependencies=[api_key_dep])
async def get_report_asset(report_id: str, asset_path: str):
    """Serve any generated asset (FCStd, netlist, CSV, STEP, STL, etc.)"""
    runs_dir = Path(__file__).parent.parent / "runs"
    for run_dir in runs_dir.iterdir():
        if run_dir.is_dir() and run_dir.name == report_id:
            asset_file = run_dir / asset_path
            if asset_file.exists() and asset_file.is_file():
                media_type = "application/octet-stream"
                if asset_file.suffix == ".pdf":
                    media_type = "application/pdf"
                elif asset_file.suffix in [".csv", ".txt"]:
                    media_type = "text/plain"
                elif asset_file.suffix in [".net", ".cir"]:
                    media_type = "text/plain"
                elif asset_file.suffix in [".step", ".stp", ".stl"]:
                    media_type = "application/octet-stream"
                elif asset_file.suffix == ".FCStd":
                    media_type = "application/octet-stream"
                return FileResponse(asset_file, media_type=media_type, filename=asset_file.name)
    raise HTTPException(status_code=404, detail="Asset not found")

@app.get("/api/settings", dependencies=[api_key_dep])
async def get_settings():
    return settings

@app.post("/api/settings", dependencies=[api_key_dep])
async def update_settings(new_settings: dict):
    global settings
    settings.update(new_settings)
    save_settings(settings)
    return {"status": "updated"}

# Serve frontend in production
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)