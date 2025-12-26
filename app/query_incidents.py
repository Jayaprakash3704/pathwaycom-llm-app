"""
Incident Query Module - Consumes Pathway Backend Outputs

This module queries incident data from the Pathway backend's outputs.
In a production deployment, this would connect to:
- Pathway's REST API connector
- Shared database/storage where Pathway writes outputs
- Message queue where Pathway publishes events

For demo purposes, this provides a local storage interface.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class IncidentRecord:
    """
    Incident record matching the schema from Pathway backend.
    
    This mirrors the IncidentSchema from pathwaycom-pathway/state/incident_store.py
    """
    incident_id: str
    anomaly_id: str
    anomaly_type: str
    severity: int
    source: str
    detected_at: str
    root_cause_analysis: str
    impact_assessment: str
    recommended_actions: List[str]
    actions_taken: List[str]
    priority_level: str
    escalation_status: str
    similar_to: Optional[str]
    tags: List[str]
    created_at: str
    
    # Human override fields (added by this interface layer)
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    manual_override: Optional[Dict[str, Any]] = None


@dataclass
class IncidentSummary:
    """Aggregated summary of incidents."""
    source: str
    total_incidents: int
    total_p1_critical: int
    total_p2_high: int
    total_p3_medium: int
    recent_anomaly_types: List[str]
    last_incident_at: str


# =============================================================================
# STORAGE INTERFACE
# =============================================================================

class IncidentStorage:
    """
    Interface to Pathway backend outputs.
    
    In production, this would connect to:
    - Pathway REST connector: pathway.io.http.rest_connector()
    - Database where Pathway writes: PostgreSQL, MongoDB, etc.
    - File-based outputs: CSV/JSON from pw.io.csv.write()
    
    For demo, uses local JSON storage to simulate backend connection.
    """
    
    def __init__(self, storage_path: str = "./storage"):
        """
        Initialize storage interface.
        
        Args:
            storage_path: Path to local storage directory (simulates backend output)
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.incidents_file = self.storage_path / "incidents.json"
        self.summaries_file = self.storage_path / "summaries.json"
    
    def get_all_incidents(self) -> List[IncidentRecord]:
        """
        Retrieve all incidents from backend.
        
        Returns:
            List of incident records
        """
        if not self.incidents_file.exists():
            return []
        
        with open(self.incidents_file, "r") as f:
            data = json.load(f)
        
        return [IncidentRecord(**item) for item in data]
    
    def get_incident_by_id(self, incident_id: str) -> Optional[IncidentRecord]:
        """
        Retrieve specific incident by ID.
        
        Args:
            incident_id: Unique incident identifier
        
        Returns:
            Incident record or None if not found
        """
        incidents = self.get_all_incidents()
        for incident in incidents:
            if incident.incident_id == incident_id:
                return incident
        return None
    
    def get_recent_incidents(
        self, 
        hours: int = 24, 
        severity_filter: Optional[int] = None
    ) -> List[IncidentRecord]:
        """
        Get incidents from the last N hours.
        
        Args:
            hours: Time window in hours
            severity_filter: Optional minimum severity level
        
        Returns:
            Filtered list of incidents
        """
        incidents = self.get_all_incidents()
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        filtered = []
        for incident in incidents:
            incident_time = datetime.fromisoformat(incident.detected_at.replace("Z", "+00:00"))
            if incident_time >= cutoff_time:
                if severity_filter is None or incident.severity >= severity_filter:
                    filtered.append(incident)
        
        return sorted(filtered, key=lambda x: x.detected_at, reverse=True)
    
    def get_incidents_by_source(self, source: str) -> List[IncidentRecord]:
        """
        Get all incidents for a specific service/source.
        
        Args:
            source: Service name (e.g., "api-gateway", "auth-service")
        
        Returns:
            Incidents from that source
        """
        incidents = self.get_all_incidents()
        return [inc for inc in incidents if inc.source == source]
    
    def get_summaries(self) -> Dict[str, IncidentSummary]:
        """
        Get pre-computed summaries from Pathway backend.
        
        These are computed by PathwayIncidentStore.compute_summaries()
        
        Returns:
            Dictionary mapping source -> summary
        """
        if not self.summaries_file.exists():
            return {}
        
        with open(self.summaries_file, "r") as f:
            data = json.load(f)
        
        return {k: IncidentSummary(**v) for k, v in data.items()}
    
    def update_incident(self, incident: IncidentRecord) -> bool:
        """
        Update incident record (for human overrides).
        
        Args:
            incident: Updated incident record
        
        Returns:
            True if successful
        """
        incidents = self.get_all_incidents()
        
        # Find and replace
        for i, existing in enumerate(incidents):
            if existing.incident_id == incident.incident_id:
                incidents[i] = incident
                break
        else:
            # Not found, append
            incidents.append(incident)
        
        # Write back
        with open(self.incidents_file, "w") as f:
            json.dump([asdict(inc) for inc in incidents], f, indent=2)
        
        return True
    
    def acknowledge_incident(
        self, 
        incident_id: str, 
        user: str
    ) -> Optional[IncidentRecord]:
        """
        Mark incident as acknowledged by human operator.
        
        Args:
            incident_id: Incident to acknowledge
            user: Username of operator
        
        Returns:
            Updated incident or None if not found
        """
        incident = self.get_incident_by_id(incident_id)
        if not incident:
            return None
        
        incident.acknowledged_by = user
        incident.acknowledged_at = datetime.utcnow().isoformat()
        
        self.update_incident(incident)
        return incident


# =============================================================================
# QUERY FUNCTIONS
# =============================================================================

class IncidentQueryService:
    """
    High-level query service for incident data.
    
    Provides business logic on top of storage interface.
    """
    
    def __init__(self, storage: IncidentStorage):
        self.storage = storage
    
    def get_dashboard_overview(self) -> Dict[str, Any]:
        """
        Get overview data for dashboard.
        
        Returns:
            Summary statistics and recent incidents
        """
        all_incidents = self.storage.get_all_incidents()
        recent = self.storage.get_recent_incidents(hours=24)
        summaries = self.storage.get_summaries()
        
        # Compute stats
        total_incidents = len(all_incidents)
        recent_incidents = len(recent)
        critical_count = len([inc for inc in recent if inc.severity >= 4])
        
        # Priority distribution
        priority_dist = {}
        for inc in recent:
            priority_dist[inc.priority_level] = priority_dist.get(inc.priority_level, 0) + 1
        
        # Anomaly types
        anomaly_types = {}
        for inc in recent:
            anomaly_types[inc.anomaly_type] = anomaly_types.get(inc.anomaly_type, 0) + 1
        
        return {
            "total_incidents": total_incidents,
            "recent_incidents_24h": recent_incidents,
            "critical_count_24h": critical_count,
            "priority_distribution": priority_dist,
            "anomaly_type_distribution": anomaly_types,
            "source_summaries": {k: asdict(v) for k, v in summaries.items()},
            "recent_incidents": [asdict(inc) for inc in recent[:10]],
        }
    
    def get_incident_details(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full details for a specific incident.
        
        Args:
            incident_id: Incident to retrieve
        
        Returns:
            Incident details with metadata
        """
        incident = self.storage.get_incident_by_id(incident_id)
        if not incident:
            return None
        
        # Find similar incidents
        similar = []
        if incident.similar_to:
            similar_inc = self.storage.get_incident_by_id(incident.similar_to)
            if similar_inc:
                similar.append(asdict(similar_inc))
        
        return {
            "incident": asdict(incident),
            "similar_incidents": similar,
        }
    
    def search_incidents(
        self,
        source: Optional[str] = None,
        severity_min: Optional[int] = None,
        anomaly_type: Optional[str] = None,
        hours: int = 168,  # 1 week
    ) -> List[Dict[str, Any]]:
        """
        Search incidents with filters.
        
        Args:
            source: Filter by service name
            severity_min: Minimum severity
            anomaly_type: Filter by anomaly type
            hours: Time window
        
        Returns:
            Matching incidents
        """
        incidents = self.storage.get_recent_incidents(hours=hours, severity_filter=severity_min)
        
        # Apply filters
        if source:
            incidents = [inc for inc in incidents if inc.source == source]
        
        if anomaly_type:
            incidents = [inc for inc in incidents if inc.anomaly_type == anomaly_type]
        
        return [asdict(inc) for inc in incidents]
