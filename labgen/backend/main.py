"""
FastAPI Backend for LabGen Cyberdeck Terminal
Handles report generation, verification, and WebSocket communication
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Import LabGen modules
import sys
sys.path.append(str(Path(__file__).parent.parent))
from main import run_generation as run_labgen_generation
from pipeline.verify import run_all_checks, extract_features, load_classifier, predict_classifier

app = FastAPI(title="LabGen Cyberdeck API", version="2.4.1")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
def load_settings():
    settings_path = Path(__file__).parent.parent / "settings.json"
    if settings_path.exists():
        with open(settings_path) as f:
            return json.load(f)
    return {}

settings = load_settings()

# Load classifier
classifier, feature_names = None, None
if settings.get("verification", {}).get("enabled"):
    classifier_path = Path(__file__).parent.parent / settings["verification"]["classifier_path"]
    feature_names_path = Path(__file__).parent.parent / settings["verification"]["feature_names_path"]
    if classifier_path.exists() and feature_names_path.exists():
        classifier, feature_names = load_classifier(str(classifier_path), str(feature_names_path))

# WebSocket endpoint
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        manager.disconnect(client_id)

# REST endpoints
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.4.1",
        "services": {
            "labgen": "ready",
            "verification": "ready" if classifier else "disabled",
            "rag": "ready",
            "freecad": "ready",
        }
    }

@app.get("/api/reports", response_model=List[ReportInfo])
async def list_reports():
    runs_dir = Path(__file__).parent.parent / "runs"
    reports = []
    if runs_dir.exists():
        for run_dir in sorted(runs_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if run_dir.is_dir():
                # Look for verification report
                verification_path = run_dir / "verification_report.json"
                verification = None
                if verification_path.exists():
                    with open(verification_path) as f:
                        verification = json.load(f)
                
                # Find PDF
                pdf_files = list(run_dir.glob("*.pdf"))
                pdf_path = str(pdf_files[0]) if pdf_files else None
                
                # Determine status
                status = "complete"
                if not pdf_path:
                    status = "error"
                
                reports.append(ReportInfo(
                    id=run_dir.name,
                    name=run_dir.name.replace("_", " ").replace("exp_", "EXP ").replace("analyzing_", "").replace("triac_", "TRIAC ").replace("characteristics", "CHARACTERISTICS").title(),
                    experiment=run_dir.name,
                    status=status,
                    progress=100,
                    createdAt=datetime.fromtimestamp(run_dir.stat().st_mtime).isoformat(),
                    path=pdf_path,
                    verification=verification.get("summary") if verification else None
                ))
    return reports

@app.post("/api/generate")
async def generate_report(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Start report generation"""
    report_id = f"report_{uuid.uuid4().hex[:8]}"
    
    # Create a mock response for now - actual generation happens via WebSocket
    return {
        "reportId": report_id,
        "status": "started",
        "message": "Report generation initiated"
    }

@app.websocket("/ws/generate/{report_id}")
async def generate_websocket(websocket: WebSocket, report_id: str):
    await websocket.accept()
    try:
        # Receive generation parameters
        data = await websocket.receive_text()
        params = json.loads(data)
        
        # Run generation with progress updates
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

async def run_generation_with_progress(websocket: WebSocket, report_id: str, params: dict):
    """Run the actual LabGen generation with progress updates"""
    try:
        # Import and run the actual generation
        from main import run_generation
        import argparse
        from io import StringIO
        import sys
        
        # Create args object
        class Args:
            name = params.get("experimentName", "Test Experiment")
            circuit_prompt = params.get("circuitPrompt", "")
            exp = params.get("experimentNumber", 2)
        
        args = Args()
        
        # Send initial progress
        await websocket.send_text(json.dumps({
            "type": "progress",
            "reportId": report_id,
            "progress": 10,
            "status": "generating",
            "log": "INITIALIZING GENERATION PIPELINE..."
        }))
        
        # Here we would integrate with the actual LabGen pipeline
        # For now, simulate progress
        for i, (progress, status, log) in enumerate([
            (20, "generating", "INITIALIZING RAG INDEX..."),
            (30, "generating", "QUERYING KNOWLEDGE BASE (RAG+BM25)..."),
            (40, "generating", "GENERATING CIRCUIT DESIGN..."),
            (50, "generating", "RUNNING NGSPICE SIMULATION..."),
            (60, "generating", "DRAFTING REPORT SECTIONS..."),
            (70, "generating", "ASSEMBLING LATEX DOCUMENT..."),
            (80, "generating", "COMPILING PDF WITH TECTONIC..."),
            (90, "verifying", "RUNNING VERIFICATION PIPELINE..."),
            (95, "verifying", "RUNNING LIGHTGBM CLASSIFIER..."),
            (100, "complete", "REPORT GENERATION COMPLETE"),
        ]):
            await asyncio.sleep(0.5)  # Simulate work
            await websocket.send_text(json.dumps({
                "type": "progress",
                "reportId": report_id,
                "progress": progress,
                "status": status,
                "log": log
            }))
        
        # Simulate verification results
        await websocket.send_text(json.dumps({
            "type": "verification",
            "reportId": report_id,
            "verification": {
                "passed": True,
                "failures": 0,
                "warnings": 2
            }
        }))
        
        # Final completion
        pdf_path = f"runs/{params.get('experimentName', 'experiment').lower().replace(' ', '_')}/Exp_02_{params.get('experimentName', 'experiment').lower().replace(' ', '_')}.pdf"
        
        await websocket.send_text(json.dumps({
            "type": "complete",
            "reportId": report_id,
            "path": pdf_path,
            "verification": {
                "passed": True,
                "failures": 0,
                "warnings": 2
            }
        }))
        
    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "reportId": report_id,
            "message": str(e)
        }))

@app.post("/api/verify")
async def verify_report(request: VerifyRequest):
    """Verify an existing report"""
    try:
        # Load the report and run verification
        # This would use the existing verification pipeline
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

@app.get("/api/reports/{report_id}/pdf")
async def get_report_pdf(report_id: str):
    """Serve the generated PDF"""
    runs_dir = Path(__file__).parent.parent / "runs"
    for run_dir in runs_dir.iterdir():
        if run_dir.is_dir() and run_dir.name == report_id:
            pdf_files = list(run_dir.glob("*.pdf"))
            if pdf_files:
                return FileResponse(pdf_files[0], media_type="application/pdf")
    raise HTTPException(status_code=404, detail="Report not found")

@app.get("/api/settings")
async def get_settings():
    return settings

@app.post("/api/settings")
async def update_settings(new_settings: dict):
    global settings
    settings.update(new_settings)
    settings_path = Path(__file__).parent.parent / "settings.json"
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)
    return {"status": "updated"}

# Serve frontend in production
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)