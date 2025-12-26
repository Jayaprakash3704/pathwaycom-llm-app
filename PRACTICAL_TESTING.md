# 🧪 Practical Testing Guide: Find Real Errors

This guide shows you how to test the interface layer with realistic data and scenarios.

---

## Quick Setup (2 minutes)

```bash
# 1. Clone and install
git clone https://github.com/Jayaprakash3704/pathwaycom-llm-app.git
cd pathwaycom-llm-app
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env: Add GROQ_API_KEY or OPENAI_API_KEY

# 3. Create mock incidents (simulate backend output)
mkdir -p storage
```

---

## Test 1: View Mock Incidents (30 seconds)

### Create Test Data

```bash
cat > storage/incidents.json << 'EOF'
[
  {
    "incident_id": "INC-2025-001",
    "anomaly_id": "ANOM-001",
    "anomaly_type": "error_spike",
    "severity": 5,
    "source": "payment-service",
    "detected_at": "2025-12-26T10:15:00Z",
    "root_cause_analysis": "Payment gateway API credentials expired at 10:00 UTC. All payment requests returning HTTP 401 Unauthorized. Impact: 100% payment failure rate affecting ~5000 active checkout sessions.",
    "impact_assessment": "CRITICAL: Revenue loss estimated at $15,000/minute. Customer support queue increased 300%. High risk of customer churn if not resolved within 15 minutes.",
    "recommended_actions": ["alert_oncall", "rotate_credentials", "failover_provider"],
    "actions_taken": ["alert_oncall"],
    "priority_level": "P1-CRITICAL",
    "escalation_status": "escalated",
    "similar_to": null,
    "tags": ["payment", "credentials", "revenue-impact"],
    "created_at": "2025-12-26T10:15:05Z",
    "acknowledged_by": null,
    "acknowledged_at": null,
    "manual_override": null
  },
  {
    "incident_id": "INC-2025-002",
    "anomaly_id": "ANOM-002",
    "anomaly_type": "high_error_rate",
    "severity": 4,
    "source": "auth-service",
    "detected_at": "2025-12-26T09:45:00Z",
    "root_cause_analysis": "Database connection pool exhausted (50/50 connections in use). Queries timing out after 5s. Root cause: Long-running queries not being closed properly after user export feature was deployed.",
    "impact_assessment": "User authentication delayed by 5-10 seconds. ~40% of login attempts timing out. New user registrations blocked.",
    "recommended_actions": ["restart_service", "scale_up", "optimize_queries"],
    "actions_taken": ["restart_service", "scale_up"],
    "priority_level": "P2-HIGH",
    "escalation_status": "auto-resolved",
    "similar_to": "INC-2025-12-20-003",
    "tags": ["auth", "database", "connection-pool"],
    "created_at": "2025-12-26T09:45:05Z",
    "acknowledged_by": "alice@company.com",
    "acknowledged_at": "2025-12-26T09:50:00Z",
    "manual_override": null
  }
]
EOF
```

### Run Dashboard

```bash
# View overview
python client/dashboard.py overview
```

**Expected Output**:
```
╔════════════════════════════════════════════════════════════╗
║           INCIDENT RESPONSE DASHBOARD                      ║
╚════════════════════════════════════════════════════════════╝

📊 OVERVIEW
  Total Incidents: 2
  Recent (24h): 2
  Critical: 1
  
🎯 PRIORITY DISTRIBUTION
  P1-CRITICAL: 1 ██████████████████████
  P2-HIGH: 1     ███████████

🔥 AFFECTED SERVICES
  payment-service: 1 incident (1 P1)
  auth-service: 1 incident (1 P2)
```

---

## Test 2: Query Incidents via API (1 minute)

### Start API Server

```bash
# Terminal 1
python main.py
```

### Test Endpoints

```bash
# Terminal 2

# 1. Get dashboard overview
curl http://localhost:8000/api/dashboard | jq .

# 2. Query critical incidents only
curl "http://localhost:8000/api/incidents?severity_min=5" | jq .

# 3. Get specific incident details
curl http://localhost:8000/api/incidents/INC-2025-001 | jq .

# 4. Search by service
curl "http://localhost:8000/api/incidents?source=payment-service" | jq .
```

**Expected**: JSON responses with incident data

---

## Test 3: Human Override Workflows (2 minutes)

### Acknowledge Incident

```bash
curl -X POST http://localhost:8000/api/incidents/INC-2025-001/acknowledge \
  -H "Content-Type: application/json" \
  -d '{
    "operator": "bob@company.com",
    "reason": "Credentials rotated manually, monitoring recovery"
  }' | jq .
```

**Expected Response**:
```json
{
  "status": "success",
  "incident_id": "INC-2025-001",
  "acknowledged_by": "bob@company.com",
  "acknowledged_at": "2025-12-26T10:20:00Z"
}
```

### Escalate Incident

```bash
curl -X POST http://localhost:8000/api/incidents/INC-2025-001/escalate \
  -H "Content-Type: application/json" \
  -d '{
    "operator": "alice@company.com",
    "to_team": "security",
    "reason": "Credentials expired - possible security issue",
    "new_priority": "P1-CRITICAL"
  }' | jq .
```

### Suppress False Positive

```bash
curl -X POST http://localhost:8000/api/incidents/INC-2025-002/suppress \
  -H "Content-Type: application/json" \
  -d '{
    "operator": "charlie@company.com",
    "reason": "Planned maintenance window, expected behavior"
  }' | jq .
```

---

## Test 4: LLM Explanations (30 seconds)

### Generate Explanation

```bash
curl -X POST http://localhost:8000/api/explain \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-2025-001",
    "explain_reasoning": true,
    "explain_actions": true,
    "explain_impact": true
  }' | jq .
```

**Expected**: Human-readable explanation from LLM

**Example Output**:
```json
{
  "incident_id": "INC-2025-001",
  "explanation": {
    "reasoning": "This incident was detected because our payment service suddenly started returning 100% HTTP 401 errors. The system monitors payment transaction success rates every 10 seconds, and when the rate dropped from 98% to 0% within 30 seconds, it triggered a critical anomaly alert...",
    "actions": "The agent recommended alerting the on-call engineer immediately because payment failures have direct revenue impact. Based on historical data, payment incidents cost an average of $15,000 per minute...",
    "impact": "This incident blocks all customer payments across the platform. With ~5000 active checkout sessions at the time of detection, we estimate $750,000 in potential lost revenue if customers abandon carts..."
  }
}
```

---

## Test 5: Real-World Scenario Simulation

### Scenario: Production Payment Outage

Create a realistic incident sequence:

```python
# simulate_payment_outage.py

import requests
import time
import json
from datetime import datetime, timezone

API_URL = "http://localhost:8000"

def create_incident(incident_data):
    """Simulate backend creating an incident"""
    # In production, this comes from Pathway backend
    # For testing, we manually create incident files
    
    with open("storage/incidents.json", "r") as f:
        incidents = json.load(f)
    
    incidents.append(incident_data)
    
    with open("storage/incidents.json", "w") as f:
        json.dump(incidents, f, indent=2)

# Simulate payment gateway failure
payment_incident = {
    "incident_id": f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
    "anomaly_id": "ANOM-PAYMENT-001",
    "anomaly_type": "error_spike",
    "severity": 5,
    "source": "payment-service",
    "detected_at": datetime.now(timezone.utc).isoformat(),
    "root_cause_analysis": "Stripe API rate limit exceeded (1000 req/sec). Traffic spike from flash sale caused 3x normal payment volume.",
    "impact_assessment": "All payment processing blocked. Flash sale conversions at 0%. Customer complaints rising.",
    "recommended_actions": ["alert_oncall", "throttle_requests", "activate_backup_processor"],
    "actions_taken": [],
    "priority_level": "P1-CRITICAL",
    "escalation_status": "needs-attention",
    "similar_to": None,
    "tags": ["payment", "rate-limit", "flash-sale"],
    "created_at": datetime.now(timezone.utc).isoformat(),
    "acknowledged_by": None,
    "acknowledged_at": None,
    "manual_override": None
}

create_incident(payment_incident)
print(f"Created incident: {payment_incident['incident_id']}")

# Wait a bit
time.sleep(2)

# SRE team acknowledges
incident_id = payment_incident['incident_id']
response = requests.post(
    f"{API_URL}/api/incidents/{incident_id}/acknowledge",
    json={
        "operator": "sre-team@company.com",
        "reason": "Investigating Stripe rate limits, activating backup processor"
    }
)
print(f"Acknowledged: {response.json()}")

# Wait
time.sleep(2)

# Generate explanation for incident report
response = requests.post(
    f"{API_URL}/api/explain",
    json={
        "incident_id": incident_id,
        "explain_reasoning": True,
        "explain_actions": True,
        "explain_impact": True
    }
)
explanation = response.json()
print("\nGenerated Explanation:")
print(json.dumps(explanation, indent=2))

# View dashboard
print("\nFinal Dashboard State:")
response = requests.get(f"{API_URL}/api/dashboard")
print(json.dumps(response.json(), indent=2))
```

**Run**:
```bash
python simulate_payment_outage.py
```

---

## Test 6: Integration with Real Backend

### Connect to Backend Output

When the backend ([pathwaycom-pathway](https://github.com/Jayaprakash3704/pathwaycom-pathway)) is running:

```python
# app/query_incidents.py - Modify storage path

class IncidentStorage:
    def __init__(self, storage_path: str = None):
        # Point to backend output directory
        if storage_path is None:
            storage_path = os.getenv(
                "BACKEND_OUTPUT_PATH",
                "../pathwaycom-pathway/output"  # Backend writes here
            )
        
        self.storage_path = Path(storage_path)
        self.incidents_file = self.storage_path / "incidents.json"
        self.summaries_file = self.storage_path / "summaries.json"
```

**Test End-to-End**:

```bash
# Terminal 1: Start backend
cd pathwaycom-pathway
python main.py

# Terminal 2: Start interface
cd pathwaycom-llm-app
export BACKEND_OUTPUT_PATH="../pathwaycom-pathway/output"
python main.py

# Terminal 3: Watch dashboard
python client/dashboard.py watch 5

# As backend detects incidents, interface will show them in real-time
```

---

## Test 7: Audit Trail Verification

### Check All Overrides

```bash
# View all human interventions
curl http://localhost:8000/api/overrides | jq .
```

**Expected Response**:
```json
{
  "total_overrides": 3,
  "overrides": [
    {
      "timestamp": "2025-12-26T10:20:00Z",
      "incident_id": "INC-2025-001",
      "action": "acknowledge",
      "operator": "bob@company.com",
      "reason": "Credentials rotated manually"
    },
    {
      "timestamp": "2025-12-26T10:21:00Z",
      "incident_id": "INC-2025-001",
      "action": "escalate",
      "operator": "alice@company.com",
      "to_team": "security",
      "reason": "Possible security issue"
    }
  ]
}
```

### Get Incident Audit Trail

```bash
curl http://localhost:8000/api/incidents/INC-2025-001/audit | jq .
```

**Expected**: Complete timeline of system and human actions

---

## Common Issues & Solutions

### Issue 1: "No incidents found"

**Solution**: Create test data
```bash
mkdir -p storage
cp ../pathwaycom-pathway/output/incidents.json storage/
# or create mock data as shown in Test 1
```

### Issue 2: "LLM explanation failed"

**Check**:
```bash
# Verify API key
echo $GROQ_API_KEY

# Test directly
curl -X POST https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": "test"}]}'
```

**Solution**: Check `.env` file has correct API key

### Issue 3: "API server not responding"

**Check**:
```bash
# See if server is running
ps aux | grep "python main.py"

# Check port
netstat -an | grep 8000

# Check logs
python main.py 2>&1 | tee api.log
```

---

## Performance Testing

### Load Test

```bash
# Install hey (HTTP load testing tool)
# Windows: scoop install hey
# Linux: sudo apt install hey

# Test query performance
hey -n 1000 -c 10 http://localhost:8000/api/dashboard

# Test explanation generation (more expensive)
hey -n 100 -c 5 -m POST -H "Content-Type: application/json" \
  -d '{"incident_id": "INC-2025-001", "explain_reasoning": true}' \
  http://localhost:8000/api/explain
```

**Expected**:
- Dashboard queries: <50ms p95
- Incident queries: <100ms p95
- Explanation generation: 2-5 seconds (LLM call)

---

## Production Readiness Checklist

Test these before deploying:

- [ ] **API responds to all endpoints** (dashboard, incidents, overrides, explain)
- [ ] **Explanations generate successfully** with configured LLM
- [ ] **Human overrides persist** and show in audit trail
- [ ] **Dashboard displays correctly** with real incident data
- [ ] **Error handling works** (invalid incident IDs, missing fields)
- [ ] **Authentication added** (JWT or API keys)
- [ ] **Rate limiting configured** (prevent API abuse)
- [ ] **CORS settings correct** (if web frontend)
- [ ] **Monitoring enabled** (Prometheus metrics, logs)
- [ ] **Database connection** (if using PostgreSQL instead of files)

---

## Quick Reference Commands

```bash
# Start API server
python main.py

# View dashboard
python client/dashboard.py overview
python client/dashboard.py recent 24
python client/dashboard.py details INC-XXX

# Test API
curl http://localhost:8000/api/dashboard | jq .
curl http://localhost:8000/api/incidents | jq .
curl -X POST http://localhost:8000/api/explain \
  -H "Content-Type: application/json" \
  -d '{"incident_id": "INC-XXX", "explain_reasoning": true}' | jq .

# Acknowledge incident
curl -X POST http://localhost:8000/api/incidents/INC-XXX/acknowledge \
  -H "Content-Type: application/json" \
  -d '{"operator": "you@company.com", "reason": "Investigating"}' | jq .

# Check API docs
open http://localhost:8000/docs  # Swagger UI
```

---

This guide helps you test the interface layer with realistic scenarios. Start with mock data, then connect to real backend output.
