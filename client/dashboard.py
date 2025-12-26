"""
Dashboard Client - Simple CLI/Terminal Interface

Provides human-readable view of:
- Active incidents
- Agent actions
- System health
- Override history

This is a minimal interface - production would use web UI.
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path


# =============================================================================
# TERMINAL UTILITIES
# =============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"


def print_header(text: str) -> None:
    """Print formatted header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.RESET}\n")


def print_section(text: str) -> None:
    """Print section divider."""
    print(f"\n{Colors.BOLD}{text}{Colors.RESET}")
    print(f"{'-'*len(text)}")


def severity_color(severity: int) -> str:
    """Get color for severity level."""
    if severity >= 4:
        return Colors.RED
    elif severity == 3:
        return Colors.YELLOW
    else:
        return Colors.GREEN


# =============================================================================
# DASHBOARD
# =============================================================================

class Dashboard:
    """
    Terminal-based dashboard for incident monitoring.
    
    In production, this would be replaced with a web UI (React, Vue, etc.)
    """
    
    def __init__(self, storage_path: str = "./storage"):
        """Initialize dashboard."""
        self.storage_path = Path(storage_path)
        
        # Import services
        import sys
        sys.path.append(str(Path(__file__).parent.parent))
        
        from app.query_incidents import IncidentStorage, IncidentQueryService
        from app.manual_override import ManualOverrideService
        
        self.storage = IncidentStorage(storage_path=storage_path)
        self.query_service = IncidentQueryService(self.storage)
        self.override_service = ManualOverrideService(storage_path=storage_path)
    
    def show_overview(self) -> None:
        """Display dashboard overview."""
        print_header("INCIDENT RESPONSE DASHBOARD")
        
        # Get overview data
        overview = self.query_service.get_dashboard_overview()
        
        # Summary stats
        print_section("📊 SYSTEM OVERVIEW (Last 24 Hours)")
        print(f"  Total Incidents: {overview['total_incidents']}")
        print(f"  Recent (24h):    {overview['recent_incidents_24h']}")
        print(f"  Critical:        {Colors.RED}{overview['critical_count_24h']}{Colors.RESET}")
        
        # Priority distribution
        print_section("🎯 PRIORITY DISTRIBUTION")
        for priority, count in sorted(overview['priority_distribution'].items()):
            color = Colors.RED if "CRITICAL" in priority or "HIGH" in priority else Colors.YELLOW
            print(f"  {color}{priority:20s}{Colors.RESET} {count:3d}")
        
        # Anomaly types
        print_section("🔍 ANOMALY TYPES")
        for anomaly_type, count in sorted(overview['anomaly_type_distribution'].items(), key=lambda x: -x[1]):
            print(f"  {anomaly_type:30s} {count:3d}")
        
        # Source summaries
        print_section("🌐 AFFECTED SERVICES")
        for source, summary in overview['source_summaries'].items():
            print(f"\n  {Colors.BOLD}{source}{Colors.RESET}")
            print(f"    Total: {summary['total_incidents']} | "
                  f"P1: {Colors.RED}{summary['total_p1_critical']}{Colors.RESET} | "
                  f"P2: {Colors.YELLOW}{summary['total_p2_high']}{Colors.RESET}")
        
        print("\n")
    
    def show_recent_incidents(self, hours: int = 24, limit: int = 10) -> None:
        """Display recent incidents."""
        print_header(f"RECENT INCIDENTS (Last {hours} hours)")
        
        incidents = self.query_service.search_incidents(hours=hours)[:limit]
        
        if not incidents:
            print(f"  {Colors.GREEN}✓ No incidents detected{Colors.RESET}\n")
            return
        
        for incident in incidents:
            severity = incident['severity']
            color = severity_color(severity)
            
            print(f"\n{color}{'▊' * 80}{Colors.RESET}")
            print(f"{color}{Colors.BOLD}Incident: {incident['incident_id']}{Colors.RESET}")
            print(f"  Source:   {incident['source']}")
            print(f"  Type:     {incident['anomaly_type']}")
            print(f"  Severity: {color}{'●' * severity}{'○' * (5-severity)}{Colors.RESET} ({severity}/5)")
            print(f"  Priority: {incident['priority_level']}")
            print(f"  Detected: {incident['detected_at']}")
            
            # Root cause (truncated)
            root_cause = incident['root_cause_analysis']
            if len(root_cause) > 100:
                root_cause = root_cause[:100] + "..."
            print(f"  Cause:    {root_cause}")
            
            # Actions taken
            if incident['actions_taken']:
                print(f"  Actions:  {', '.join(incident['actions_taken'][:3])}")
            
            # Acknowledgement status
            if incident.get('acknowledged_by'):
                print(f"  {Colors.GREEN}✓ Acknowledged by {incident['acknowledged_by']}{Colors.RESET}")
            else:
                print(f"  {Colors.YELLOW}⚠ Needs acknowledgement{Colors.RESET}")
        
        print("\n")
    
    def show_incident_details(self, incident_id: str) -> None:
        """Display detailed incident information."""
        details = self.query_service.get_incident_details(incident_id)
        
        if not details:
            print(f"{Colors.RED}✗ Incident {incident_id} not found{Colors.RESET}\n")
            return
        
        incident = details['incident']
        
        print_header(f"INCIDENT DETAILS: {incident_id}")
        
        # Basic info
        print_section("📋 BASIC INFORMATION")
        print(f"  ID:           {incident['incident_id']}")
        print(f"  Anomaly ID:   {incident['anomaly_id']}")
        print(f"  Type:         {incident['anomaly_type']}")
        print(f"  Severity:     {severity_color(incident['severity'])}{'●' * incident['severity']}{Colors.RESET} ({incident['severity']}/5)")
        print(f"  Priority:     {incident['priority_level']}")
        print(f"  Source:       {incident['source']}")
        print(f"  Detected:     {incident['detected_at']}")
        print(f"  Created:      {incident['created_at']}")
        
        # Agent analysis
        print_section("🤖 AGENT ANALYSIS")
        print(f"  Root Cause:")
        print(f"    {incident['root_cause_analysis']}")
        print(f"\n  Impact Assessment:")
        print(f"    {incident['impact_assessment']}")
        
        # Recommended actions
        print_section("💡 RECOMMENDED ACTIONS")
        for i, action in enumerate(incident['recommended_actions'], 1):
            print(f"  {i}. {action}")
        
        # Actions taken
        print_section("✅ ACTIONS TAKEN")
        for i, action in enumerate(incident['actions_taken'], 1):
            print(f"  {i}. {Colors.GREEN}{action}{Colors.RESET}")
        
        # Escalation
        print_section("🚨 ESCALATION STATUS")
        print(f"  Status: {incident['escalation_status']}")
        
        # Tags
        if incident['tags']:
            print_section("🏷️  TAGS")
            print(f"  {', '.join(incident['tags'])}")
        
        # Acknowledgement
        print_section("👤 HUMAN OVERSIGHT")
        if incident.get('acknowledged_by'):
            print(f"  {Colors.GREEN}✓ Acknowledged by {incident['acknowledged_by']}{Colors.RESET}")
            print(f"  At: {incident.get('acknowledged_at', 'N/A')}")
        else:
            print(f"  {Colors.YELLOW}⚠ Awaiting acknowledgement{Colors.RESET}")
        
        # Audit trail
        audit_trail = self.override_service.get_audit_trail(incident_id)
        if audit_trail:
            print_section("📜 AUDIT TRAIL")
            for event in audit_trail[-5:]:  # Last 5 events
                print(f"  [{event['timestamp']}] {event['type']}: {event['action']}")
                print(f"    Operator: {event['operator']}")
                print(f"    Reason: {event['reason']}")
        
        print("\n")
    
    def show_override_history(self, limit: int = 20) -> None:
        """Display recent manual overrides."""
        print_header("MANUAL OVERRIDE HISTORY")
        
        overrides = self.override_service.get_override_history(limit=limit)
        
        if not overrides:
            print(f"  {Colors.GREEN}No manual overrides recorded{Colors.RESET}\n")
            return
        
        for override in overrides:
            print(f"\n  {Colors.BOLD}[{override.timestamp}]{Colors.RESET}")
            print(f"  Override ID:  {override.override_id}")
            print(f"  Incident ID:  {override.incident_id}")
            print(f"  Action:       {Colors.YELLOW}{override.action}{Colors.RESET}")
            print(f"  Operator:     {override.operator}")
            print(f"  Reason:       {override.reason}")
        
        print("\n")
    
    def watch_mode(self, refresh_seconds: int = 10) -> None:
        """
        Continuous monitoring mode (refreshes every N seconds).
        
        Args:
            refresh_seconds: Refresh interval
        """
        try:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                self.show_overview()
                self.show_recent_incidents(hours=1, limit=5)
                
                print(f"{Colors.CYAN}Refreshing every {refresh_seconds}s... (Ctrl+C to exit){Colors.RESET}")
                time.sleep(refresh_seconds)
        
        except KeyboardInterrupt:
            print(f"\n{Colors.GREEN}✓ Monitoring stopped{Colors.RESET}\n")


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """Main CLI entry point."""
    import sys
    
    dashboard = Dashboard()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python dashboard.py overview")
        print("  python dashboard.py recent [hours]")
        print("  python dashboard.py details <incident_id>")
        print("  python dashboard.py overrides")
        print("  python dashboard.py watch [refresh_seconds]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "overview":
        dashboard.show_overview()
    
    elif command == "recent":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        dashboard.show_recent_incidents(hours=hours)
    
    elif command == "details":
        if len(sys.argv) < 3:
            print("Usage: python dashboard.py details <incident_id>")
            sys.exit(1)
        incident_id = sys.argv[2]
        dashboard.show_incident_details(incident_id)
    
    elif command == "overrides":
        dashboard.show_override_history()
    
    elif command == "watch":
        refresh = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        dashboard.watch_mode(refresh_seconds=refresh)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
