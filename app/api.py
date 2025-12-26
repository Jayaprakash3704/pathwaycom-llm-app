"""
FastAPI Application - REST Interface for Incident Management

Provides HTTP endpoints to:
- Query incidents from Pathway backend
- View agent decisions and actions
- Perform human-in-the-loop overrides
- Explain decisions using LLM

This is the INTERFACE layer - NO streaming logic, NO agent orchestration.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

# Local imports
from .query_incidents import (
    IncidentStorage,
    IncidentQueryService,
    IncidentRecord,
)
from .manual_override import (
    ManualOverrideService,
    OverrideAction,
)


# =============================================================================
# API MODELS
# =============================================================================

class AcknowledgeRequest(BaseModel):
    """Request to acknowledge an incident."""
    operator: str = Field(..., description="Username of operator")
    reason: str = Field(default="Acknowledged by operator", description="Optional reason")


class SuppressRequest(BaseModel):
    """Request to suppress a false positive."""
    operator: str
    reason: str = Field(..., min_length=10, description="Detailed reason required")


class EscalateRequest(BaseModel):
    """Request to escalate an incident."""
    operator: str
    to_team: str = Field(..., description="Target team name")
    reason: str
    new_priority: Optional[str] = None


class ModifyPriorityRequest(BaseModel):
    """Request to change incident priority."""
    operator: str
    new_priority: str = Field(..., pattern="^P[1-5]-(CRITICAL|HIGH|MEDIUM|LOW)$")
    reason: str


class CancelActionRequest(BaseModel):
    """Request to cancel an agent action."""
    operator: str
    action_name: str
    reason: str


class ForceActionRequest(BaseModel):
    """Request to force an action."""
    operator: str
    action_name: str
    action_params: Dict[str, Any] = {}
    reason: str


class ExplainRequest(BaseModel):
    """Request to explain incident using LLM."""
    incident_id: str
    explain_reasoning: bool = True
    explain_actions: bool = True
    explain_impact: bool = True


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="Pathway Incident Management API",
    description="Interface layer for agentic incident response backend",
    version="1.0.0",
)

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
storage = IncidentStorage()
query_service = IncidentQueryService(storage)
override_service = ManualOverrideService()


# =============================================================================
# QUERY ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """API health check."""
    return {
        "service": "Pathway Incident Management API",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/dashboard")
async def get_dashboard():
    """
    Get dashboard overview with incident statistics.
    
    Returns summary data for the last 24 hours.
    """
    try:
        overview = query_service.get_dashboard_overview()
        return JSONResponse(content=overview)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard query failed: {str(e)}")


@app.get("/api/incidents")
async def list_incidents(
    source: Optional[str] = Query(None, description="Filter by service name"),
    severity_min: Optional[int] = Query(None, ge=1, le=5, description="Minimum severity"),
    anomaly_type: Optional[str] = Query(None, description="Filter by anomaly type"),
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
):
    """
    Search incidents with optional filters.
    
    Query Parameters:
    - source: Service name (e.g., "api-gateway")
    - severity_min: Minimum severity (1-5)
    - anomaly_type: Type of anomaly
    - hours: Time window (default 24h, max 1 week)
    """
    try:
        incidents = query_service.search_incidents(
            source=source,
            severity_min=severity_min,
            anomaly_type=anomaly_type,
            hours=hours,
        )
        return JSONResponse(content={"incidents": incidents, "count": len(incidents)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Incident search failed: {str(e)}")


@app.get("/api/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """
    Get detailed information about a specific incident.
    
    Includes:
    - Full incident record
    - Agent reasoning and decisions
    - Actions taken
    - Similar past incidents
    """
    details = query_service.get_incident_details(incident_id)
    
    if not details:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    
    return JSONResponse(content=details)


@app.get("/api/incidents/{incident_id}/audit")
async def get_incident_audit(incident_id: str):
    """
    Get complete audit trail for an incident.
    
    Shows chronological timeline of:
    - Agent actions
    - Manual overrides
    - State changes
    """
    # Verify incident exists
    details = query_service.get_incident_details(incident_id)
    if not details:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    
    audit_trail = override_service.get_audit_trail(incident_id)
    
    return JSONResponse(content={
        "incident_id": incident_id,
        "audit_trail": audit_trail,
        "total_events": len(audit_trail),
    })


@app.get("/api/summaries")
async def get_summaries():
    """
    Get pre-computed summaries by source.
    
    These are generated by Pathway backend's aggregation pipelines.
    """
    try:
        summaries = storage.get_summaries()
        return JSONResponse(content={"summaries": summaries})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary query failed: {str(e)}")


# =============================================================================
# OVERRIDE ENDPOINTS
# =============================================================================

@app.post("/api/incidents/{incident_id}/acknowledge")
async def acknowledge_incident(incident_id: str, request: AcknowledgeRequest):
    """
    Acknowledge an incident (operator is aware and monitoring).
    """
    # Verify incident exists
    incident = storage.get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    
    try:
        override = override_service.acknowledge_incident(
            incident_id=incident_id,
            operator=request.operator,
            reason=request.reason,
        )
        
        # Update incident record
        storage.acknowledge_incident(incident_id, request.operator)
        
        return JSONResponse(content={
            "success": True,
            "override_id": override.override_id,
            "message": f"Incident acknowledged by {request.operator}",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Acknowledge failed: {str(e)}")


@app.post("/api/incidents/{incident_id}/suppress")
async def suppress_incident(incident_id: str, request: SuppressRequest):
    """
    Suppress an incident (false positive or non-actionable).
    
    Requires detailed reason for audit trail.
    """
    # Verify incident exists
    incident = storage.get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    
    try:
        override = override_service.suppress_incident(
            incident_id=incident_id,
            operator=request.operator,
            reason=request.reason,
        )
        
        return JSONResponse(content={
            "success": True,
            "override_id": override.override_id,
            "message": f"Incident suppressed by {request.operator}",
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suppress failed: {str(e)}")


@app.post("/api/incidents/{incident_id}/escalate")
async def escalate_incident(incident_id: str, request: EscalateRequest):
    """
    Escalate incident to different team or priority.
    """
    # Verify incident exists
    incident = storage.get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    
    try:
        override = override_service.escalate_incident(
            incident_id=incident_id,
            operator=request.operator,
            to_team=request.to_team,
            reason=request.reason,
            new_priority=request.new_priority,
        )
        
        return JSONResponse(content={
            "success": True,
            "override_id": override.override_id,
            "message": f"Incident escalated to {request.to_team}",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Escalate failed: {str(e)}")


@app.post("/api/incidents/{incident_id}/modify-priority")
async def modify_priority(incident_id: str, request: ModifyPriorityRequest):
    """
    Change incident priority.
    
    Priority format: P1-CRITICAL, P2-HIGH, P3-MEDIUM, P4-LOW, P5-TRIVIAL
    """
    # Verify incident exists
    incident = storage.get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    
    try:
        override = override_service.modify_priority(
            incident_id=incident_id,
            operator=request.operator,
            new_priority=request.new_priority,
            reason=request.reason,
        )
        
        return JSONResponse(content={
            "success": True,
            "override_id": override.override_id,
            "message": f"Priority changed to {request.new_priority}",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Modify priority failed: {str(e)}")


@app.post("/api/incidents/{incident_id}/cancel-action")
async def cancel_action(incident_id: str, request: CancelActionRequest):
    """
    Cancel a planned or in-progress agent action.
    """
    # Verify incident exists
    incident = storage.get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    
    try:
        override = override_service.cancel_action(
            incident_id=incident_id,
            operator=request.operator,
            action_name=request.action_name,
            reason=request.reason,
        )
        
        return JSONResponse(content={
            "success": True,
            "override_id": override.override_id,
            "message": f"Action '{request.action_name}' cancelled",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cancel action failed: {str(e)}")


@app.post("/api/incidents/{incident_id}/force-action")
async def force_action(incident_id: str, request: ForceActionRequest):
    """
    Force execution of action not recommended by agents.
    
    Use with caution - bypasses agent reasoning.
    """
    # Verify incident exists
    incident = storage.get_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    
    try:
        override = override_service.force_action(
            incident_id=incident_id,
            operator=request.operator,
            action_name=request.action_name,
            action_params=request.action_params,
            reason=request.reason,
        )
        
        return JSONResponse(content={
            "success": True,
            "override_id": override.override_id,
            "message": f"Action '{request.action_name}' forced",
            "warning": "Action executed outside agent recommendations",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Force action failed: {str(e)}")


# =============================================================================
# EXPLANATION ENDPOINT
# =============================================================================

@app.post("/api/explain")
async def explain_incident(request: ExplainRequest):
    """
    Generate human-readable explanation of incident using LLM.
    
    Explains:
    - Why the anomaly was detected
    - Agent reasoning process
    - Why specific actions were recommended
    - Expected impact
    """
    # Verify incident exists
    details = query_service.get_incident_details(request.incident_id)
    if not details:
        raise HTTPException(status_code=404, detail=f"Incident {request.incident_id} not found")
    
    try:
        from ..llm.explanation_generator import ExplanationGenerator
        
        generator = ExplanationGenerator()
        explanation = generator.generate_explanation(
            incident=details["incident"],
            explain_reasoning=request.explain_reasoning,
            explain_actions=request.explain_actions,
            explain_impact=request.explain_impact,
        )
        
        return JSONResponse(content={
            "incident_id": request.incident_id,
            "explanation": explanation,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation generation failed: {str(e)}")


# =============================================================================
# OVERRIDE HISTORY
# =============================================================================

@app.get("/api/overrides")
async def list_overrides(
    incident_id: Optional[str] = Query(None, description="Filter by incident"),
    operator: Optional[str] = Query(None, description="Filter by operator"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
):
    """
    Get history of manual overrides.
    
    Useful for:
    - Audit compliance
    - Operator activity tracking
    - System training (learn from human corrections)
    """
    try:
        overrides = override_service.get_override_history(
            incident_id=incident_id,
            operator=operator,
            limit=limit,
        )
        
        return JSONResponse(content={
            "overrides": [
                {
                    "override_id": o.override_id,
                    "incident_id": o.incident_id,
                    "action": o.action,
                    "operator": o.operator,
                    "timestamp": o.timestamp,
                    "reason": o.reason,
                }
                for o in overrides
            ],
            "count": len(overrides),
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Override query failed: {str(e)}")
