"""
Manual Override Module - Human-in-the-Loop Actions

Allows human operators to:
- Acknowledge incidents
- Override agent decisions
- Escalate to different teams
- Suppress false positives
- Trigger manual actions

This demonstrates responsible AI deployment where humans remain in control.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


# =============================================================================
# OVERRIDE TYPES
# =============================================================================

class OverrideAction(str, Enum):
    """Types of manual overrides."""
    ACKNOWLEDGE = "acknowledge"
    SUPPRESS = "suppress"
    ESCALATE = "escalate"
    MODIFY_PRIORITY = "modify_priority"
    CANCEL_ACTION = "cancel_action"
    FORCE_ACTION = "force_action"


@dataclass
class ManualOverride:
    """Record of a manual override."""
    override_id: str
    incident_id: str
    action: OverrideAction
    operator: str
    timestamp: str
    reason: str
    previous_state: Dict[str, Any]
    new_state: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


# =============================================================================
# OVERRIDE SERVICE
# =============================================================================

class ManualOverrideService:
    """
    Service for human-in-the-loop interventions.
    
    Maintains audit trail of all manual actions for compliance and debugging.
    """
    
    def __init__(self, storage_path: str = "./storage"):
        """Initialize override service."""
        from pathlib import Path
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.overrides_file = self.storage_path / "overrides.json"
    
    def _generate_override_id(self) -> str:
        """Generate unique override ID."""
        import uuid
        return f"OVR-{uuid.uuid4().hex[:12].upper()}"
    
    def _load_overrides(self) -> List[ManualOverride]:
        """Load override history."""
        if not self.overrides_file.exists():
            return []
        
        with open(self.overrides_file, "r") as f:
            data = json.load(f)
        
        return [ManualOverride(**item) for item in data]
    
    def _save_overrides(self, overrides: List[ManualOverride]) -> None:
        """Save override history."""
        with open(self.overrides_file, "w") as f:
            json.dump([asdict(ovr) for ovr in overrides], f, indent=2)
    
    def acknowledge_incident(
        self,
        incident_id: str,
        operator: str,
        reason: str = "Acknowledged by operator",
    ) -> ManualOverride:
        """
        Acknowledge an incident - operator is aware and monitoring.
        
        Args:
            incident_id: Incident to acknowledge
            operator: Username
            reason: Optional explanation
        
        Returns:
            Override record
        """
        override = ManualOverride(
            override_id=self._generate_override_id(),
            incident_id=incident_id,
            action=OverrideAction.ACKNOWLEDGE,
            operator=operator,
            timestamp=datetime.utcnow().isoformat(),
            reason=reason,
            previous_state={"acknowledged": False},
            new_state={"acknowledged": True, "acknowledged_by": operator},
        )
        
        # Save to audit trail
        overrides = self._load_overrides()
        overrides.append(override)
        self._save_overrides(overrides)
        
        print(f"[OVERRIDE] Incident {incident_id} acknowledged by {operator}")
        return override
    
    def suppress_incident(
        self,
        incident_id: str,
        operator: str,
        reason: str,
    ) -> ManualOverride:
        """
        Suppress a false positive or non-actionable incident.
        
        Args:
            incident_id: Incident to suppress
            operator: Username
            reason: Required explanation for suppression
        
        Returns:
            Override record
        """
        if not reason or len(reason) < 10:
            raise ValueError("Suppression requires detailed reason (min 10 chars)")
        
        override = ManualOverride(
            override_id=self._generate_override_id(),
            incident_id=incident_id,
            action=OverrideAction.SUPPRESS,
            operator=operator,
            timestamp=datetime.utcnow().isoformat(),
            reason=reason,
            previous_state={"suppressed": False},
            new_state={"suppressed": True, "suppressed_by": operator},
        )
        
        overrides = self._load_overrides()
        overrides.append(override)
        self._save_overrides(overrides)
        
        print(f"[OVERRIDE] Incident {incident_id} suppressed by {operator}: {reason}")
        return override
    
    def escalate_incident(
        self,
        incident_id: str,
        operator: str,
        to_team: str,
        reason: str,
        new_priority: Optional[str] = None,
    ) -> ManualOverride:
        """
        Escalate incident to different team or priority.
        
        Args:
            incident_id: Incident to escalate
            operator: Username
            to_team: Target team (e.g., "security", "platform", "database")
            reason: Escalation justification
            new_priority: Optional new priority level
        
        Returns:
            Override record
        """
        previous_state = {"escalated": False}
        new_state = {
            "escalated": True,
            "escalated_to": to_team,
            "escalated_by": operator,
        }
        
        if new_priority:
            previous_state["priority"] = None  # Would fetch from incident
            new_state["priority"] = new_priority
        
        override = ManualOverride(
            override_id=self._generate_override_id(),
            incident_id=incident_id,
            action=OverrideAction.ESCALATE,
            operator=operator,
            timestamp=datetime.utcnow().isoformat(),
            reason=reason,
            previous_state=previous_state,
            new_state=new_state,
            metadata={"target_team": to_team},
        )
        
        overrides = self._load_overrides()
        overrides.append(override)
        self._save_overrides(overrides)
        
        print(f"[OVERRIDE] Incident {incident_id} escalated to {to_team} by {operator}")
        return override
    
    def modify_priority(
        self,
        incident_id: str,
        operator: str,
        new_priority: str,
        reason: str,
    ) -> ManualOverride:
        """
        Change incident priority (e.g., P3-MEDIUM → P1-CRITICAL).
        
        Args:
            incident_id: Incident to modify
            operator: Username
            new_priority: New priority level
            reason: Justification for change
        
        Returns:
            Override record
        """
        override = ManualOverride(
            override_id=self._generate_override_id(),
            incident_id=incident_id,
            action=OverrideAction.MODIFY_PRIORITY,
            operator=operator,
            timestamp=datetime.utcnow().isoformat(),
            reason=reason,
            previous_state={"priority": "unknown"},  # Would fetch from incident
            new_state={"priority": new_priority},
        )
        
        overrides = self._load_overrides()
        overrides.append(override)
        self._save_overrides(overrides)
        
        print(f"[OVERRIDE] Incident {incident_id} priority changed to {new_priority} by {operator}")
        return override
    
    def cancel_action(
        self,
        incident_id: str,
        operator: str,
        action_name: str,
        reason: str,
    ) -> ManualOverride:
        """
        Cancel a planned or in-progress agent action.
        
        Args:
            incident_id: Related incident
            operator: Username
            action_name: Action to cancel (e.g., "restart_service")
            reason: Cancellation reason
        
        Returns:
            Override record
        """
        override = ManualOverride(
            override_id=self._generate_override_id(),
            incident_id=incident_id,
            action=OverrideAction.CANCEL_ACTION,
            operator=operator,
            timestamp=datetime.utcnow().isoformat(),
            reason=reason,
            previous_state={"action_status": "planned"},
            new_state={"action_status": "cancelled"},
            metadata={"cancelled_action": action_name},
        )
        
        overrides = self._load_overrides()
        overrides.append(override)
        self._save_overrides(overrides)
        
        print(f"[OVERRIDE] Action '{action_name}' cancelled for {incident_id} by {operator}")
        return override
    
    def force_action(
        self,
        incident_id: str,
        operator: str,
        action_name: str,
        action_params: Dict[str, Any],
        reason: str,
    ) -> ManualOverride:
        """
        Force execution of action not recommended by agents.
        
        Args:
            incident_id: Related incident
            operator: Username
            action_name: Action to force
            action_params: Action parameters
            reason: Justification for forcing
        
        Returns:
            Override record
        """
        override = ManualOverride(
            override_id=self._generate_override_id(),
            incident_id=incident_id,
            action=OverrideAction.FORCE_ACTION,
            operator=operator,
            timestamp=datetime.utcnow().isoformat(),
            reason=reason,
            previous_state={"manual_action": None},
            new_state={"manual_action": action_name, "params": action_params},
            metadata={"forced_action": action_name, "params": action_params},
        )
        
        overrides = self._load_overrides()
        overrides.append(override)
        self._save_overrides(overrides)
        
        print(f"[OVERRIDE] Action '{action_name}' forced for {incident_id} by {operator}")
        return override
    
    def get_override_history(
        self,
        incident_id: Optional[str] = None,
        operator: Optional[str] = None,
        limit: int = 100,
    ) -> List[ManualOverride]:
        """
        Get override history with optional filters.
        
        Args:
            incident_id: Filter by incident
            operator: Filter by operator
            limit: Max results
        
        Returns:
            List of overrides
        """
        overrides = self._load_overrides()
        
        # Filter
        if incident_id:
            overrides = [o for o in overrides if o.incident_id == incident_id]
        
        if operator:
            overrides = [o for o in overrides if o.operator == operator]
        
        # Sort by timestamp (most recent first)
        overrides.sort(key=lambda x: x.timestamp, reverse=True)
        
        return overrides[:limit]
    
    def get_audit_trail(self, incident_id: str) -> List[Dict[str, Any]]:
        """
        Get complete audit trail for an incident.
        
        Shows all automated actions + manual overrides.
        
        Args:
            incident_id: Incident to audit
        
        Returns:
            Chronological list of all actions
        """
        overrides = self.get_override_history(incident_id=incident_id)
        
        # Build timeline
        timeline = []
        for override in overrides:
            timeline.append({
                "timestamp": override.timestamp,
                "type": "manual_override",
                "action": override.action,
                "operator": override.operator,
                "reason": override.reason,
                "changes": {
                    "from": override.previous_state,
                    "to": override.new_state,
                },
            })
        
        # Sort chronologically
        timeline.sort(key=lambda x: x["timestamp"])
        
        return timeline
