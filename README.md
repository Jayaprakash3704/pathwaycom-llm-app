# Pathway Incident Management - Interface Layer

**This is the INTERFACE + CONTROL LAYER for the agentic incident response system.**

> **Agentic Backend**: For real-time log processing, anomaly detection, and autonomous incident response, see the companion repository: [pathwaycom-pathway](https://github.com/Jayaprakash3704/pathwaycom-pathway)

## What This Repository Does

This application provides **human/system interaction** with the automated incident response backend (see [pathwaycom-pathway](https://github.com/Jayaprakash3704/pathwaycom-pathway)).

### Core Functions

1. **Query Incidents** - Retrieve incident data from Pathway backend outputs
2. **Human Oversight** - Allow operators to acknowledge, override, or escalate incidents
3. **Explain Decisions** - Use LLM to explain agent reasoning in human language
4. **Audit Trail** - Track all manual interventions for compliance

### What This Does **NOT** Do

❌ **No streaming logic** - that lives in the backend  
❌ **No Pathway pipelines** - backend handles real-time processing  
❌ **No agent orchestration** - LangGraph agents run in the backend  

This is pure interface - queries, explanations, and human control.

---

## Architecture: How the Two Repos Connect

```
┌─────────────────────────────────────────────────────────────────┐
│                    pathwaycom-pathway                           │
│                    (AGENTIC BACKEND)                            │
│                                                                 │
│  • Real-time log ingestion (Pathway streaming)                 │
│  • Anomaly detection (windowed aggregations)                   │
│  • 5-agent system (LangGraph orchestration)                    │
│  • Incident response (automated actions)                       │
│  • State management (Pathway tables)                           │
│                                                                 │
│  OUTPUTS:                                                       │
│    ├─ incidents.json     (incident records)                    │
│    ├─ summaries.json     (aggregated stats)                    │
│    └─ Pathway tables     (continuous state)                    │
└─────────────────────────────────────────────────────────────────┘
                           ⬇ ️
            (Shared storage / REST API / Message queue)
                           ⬇️
┌─────────────────────────────────────────────────────────────────┐
│                   pathwaycom-llm-app                            │
│                   (INTERFACE LAYER - THIS REPO)                 │
│                                                                 │
│  • REST API (FastAPI)                                          │
│    - GET /api/incidents (query with filters)                   │
│    - GET /api/dashboard (overview stats)                       │
│    - POST /api/incidents/{id}/acknowledge                      │
│    - POST /api/incidents/{id}/escalate                         │
│    - POST /api/explain (LLM explanations)                      │
│                                                                 │
│  • Human-in-the-Loop Actions                                   │
│    - Acknowledge incidents                                     │
│    - Suppress false positives                                  │
│    - Override agent decisions                                  │
│    - Force manual actions                                      │
│                                                                 │
│  • LLM Explanations                                            │
│    - "Why was this detected?"                                  │
│    - "Why did agents choose these actions?"                    │
│    - "What's the business impact?"                             │
│                                                                 │
│  • Simple Dashboard (CLI)                                      │
│    - View active incidents                                     │
│    - Monitor system health                                     │
│    - Review audit trail                                        │
└─────────────────────────────────────────────────────────────────┘
```

### Key Connection Points

**In this demo:**
- Backend writes `./storage/incidents.json` and `./storage/summaries.json`
- Interface layer reads these files for incident data

**In production:**
- Pathway backend exposes REST connector: `pw.io.http.rest_connector()`
- Interface queries Pathway API: `GET http://backend:8080/incidents`
- Or shared database: Pathway writes to PostgreSQL, interface reads from same DB
- Or message queue: Pathway publishes events, interface subscribes

The pattern: **Backend generates decisions continuously, interface exposes them responsibly.**

---

## Repository Structure

```
pathwaycom-llm-app/
│
├── app/
│   ├── api.py                  # FastAPI REST endpoints
│   ├── query_incidents.py      # Query Pathway outputs
│   └── manual_override.py      # Human-in-the-loop actions
│
├── llm/
│   └── explanation_generator.py # LLM-powered explanations
│
├── client/
│   └── dashboard.py            # Terminal dashboard (CLI)
│
├── main.py                     # FastAPI server entry point
├── requirements.txt            # Dependencies
├── .env.example                # Configuration template
└── README.md                   # This file
```

---

## What the App Shows

### 1. Dashboard Overview (`GET /api/dashboard`)

```json
{
  "total_incidents": 42,
  "recent_incidents_24h": 8,
  "critical_count_24h": 2,
  "priority_distribution": {
    "P1-CRITICAL": 2,
    "P2-HIGH": 3,
    "P3-MEDIUM": 3
  },
  "source_summaries": {
    "auth-service": {
      "total_incidents": 5,
      "total_p1_critical": 1,
      "recent_anomaly_types": ["error_spike", "high_error_rate"]
    }
  }
}
```

### 2. Incident Details (`GET /api/incidents/{id}`)

```json
{
  "incident_id": "INC-ABC123",
  "anomaly_type": "error_spike",
  "severity": 4,
  "source": "auth-service",
  "root_cause_analysis": "Sudden spike in authentication failures...",
  "impact_assessment": "User login operations degraded...",
  "recommended_actions": ["alert_oncall", "restart_service"],
  "actions_taken": ["alert_oncall", "restart_service"],
  "priority_level": "P2-HIGH"
}
```

### 3. Human Explanations (`POST /api/explain`)

```json
{
  "incident_id": "INC-ABC123",
  "explanation": {
    "summary": "Auth service experienced error spike - automated restart executed",
    "reasoning": "The system detected a sudden 400% increase in authentication errors...",
    "actions": "The agent recommended restarting the service because...",
    "impact": "This incident affects all user login operations..."
  }
}
```

---

## How Humans Interact with the System

### Acknowledge Incident
```bash
curl -X POST http://localhost:8000/api/incidents/INC-ABC123/acknowledge \
  -H "Content-Type: application/json" \
  -d '{"operator": "alice", "reason": "Monitoring resolution"}'
```

### Suppress False Positive
```bash
curl -X POST http://localhost:8000/api/incidents/INC-ABC123/suppress \
  -H "Content-Type: application/json" \
  -d '{"operator": "bob", "reason": "Known test spike, not production issue"}'
```

### Escalate to Different Team
```bash
curl -X POST http://localhost:8000/api/incidents/INC-ABC123/escalate \
  -H "Content-Type: application/json" \
  -d '{"operator": "carol", "to_team": "security", "reason": "Potential breach", "new_priority": "P1-CRITICAL"}'
```

### Cancel Agent Action
```bash
curl -X POST http://localhost:8000/api/incidents/INC-ABC123/cancel-action \
  -H "Content-Type: application/json" \
  -d '{"operator": "dave", "action_name": "restart_service", "reason": "Investigating root cause first"}'
```

### Force Manual Action
```bash
curl -X POST http://localhost:8000/api/incidents/INC-ABC123/force-action \
  -H "Content-Type: application/json" \
  -d '{"operator": "eve", "action_name": "rollback_deploy", "action_params": {"version": "v1.2.3"}, "reason": "Emergency rollback required"}'
```

---

## How to Run

### 1. Setup Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys and settings
cp .env.example .env
# Edit .env with your configuration:
# - OPENAI_API_KEY or GROQ_API_KEY (for LLM explanations)
# - LLM_MODEL (e.g., llama-3.3-70b-versatile, gpt-4o-mini)
# - LLM_BASE_URL (e.g., https://api.groq.com/openai/v1 for Groq)
# - API_HOST and API_PORT for the server
# - STORAGE_PATH for incident data location
```

### Environment Variables

**LLM Configuration** (for explanation generation):
- `GROQ_API_KEY` or `OPENAI_API_KEY` - API key for LLM provider
- `LLM_MODEL` - Model name for explanations (default: `llama-3.3-70b-versatile`)
- `LLM_BASE_URL` - API endpoint (default: `https://api.groq.com/openai/v1`)
- `LLM_TEMPERATURE` - Temperature for explanations (default: 0.7)

**Server Configuration**:
- `API_HOST` - Server host (default: `0.0.0.0`)
- `API_PORT` - Server port (default: `8000`)
- `STORAGE_PATH` - Path to incident data (default: `./storage`)

### 2. Start the API Server

```bash
python main.py
```

Server starts at `http://localhost:8000`

**API Documentation:** http://localhost:8000/docs (automatic Swagger UI)

### 3. Use the Dashboard (Optional)

```bash
# View overview
python client/dashboard.py overview

# Show recent incidents
python client/dashboard.py recent 24

# Get incident details
python client/dashboard.py details INC-ABC123

# View override history
python client/dashboard.py overrides

# Watch mode (continuous monitoring)
python client/dashboard.py watch 10
```

### 4. Query via API

```bash
# Get dashboard overview
curl http://localhost:8000/api/dashboard

# List recent incidents
curl "http://localhost:8000/api/incidents?hours=24&severity_min=3"

# Get incident details
curl http://localhost:8000/api/incidents/INC-ABC123

# Get audit trail
curl http://localhost:8000/api/incidents/INC-ABC123/audit

# Explain incident
curl -X POST http://localhost:8000/api/explain \
  -H "Content-Type: application/json" \
  -d '{"incident_id": "INC-ABC123", "explain_reasoning": true}'
```

---

## Testing with Mock Data

For demo purposes, you can create mock incident data:

```bash
mkdir -p storage

# Create mock incident
cat > storage/incidents.json << 'EOF'
[
  {
    "incident_id": "INC-DEMO001",
    "anomaly_id": "ANOM-001",
    "anomaly_type": "error_spike",
    "severity": 4,
    "source": "auth-service",
    "detected_at": "2025-12-26T10:30:00Z",
    "root_cause_analysis": "Sudden spike in authentication failures due to database connection pool exhaustion",
    "impact_assessment": "User login operations degraded, 40% failure rate detected",
    "recommended_actions": ["alert_oncall", "restart_service", "scale_up"],
    "actions_taken": ["alert_oncall", "restart_service"],
    "priority_level": "P2-HIGH",
    "escalation_status": "auto-resolved",
    "similar_to": null,
    "tags": ["auth", "database", "connection-pool"],
    "created_at": "2025-12-26T10:30:05Z",
    "acknowledged_by": null,
    "acknowledged_at": null
  }
]
EOF
```

Now you can query this via the API.

---

## How This Consumes Pathway Output

### Option 1: Local File Storage (Demo)

```python
# Backend writes (in pathwaycom-pathway)
pw.io.json.write(incidents, "./storage/incidents.json")

# Interface reads (in this repo)
with open("./storage/incidents.json") as f:
    incidents = json.load(f)
```

### Option 2: Pathway REST Connector (Production)

```python
# Backend exposes (in pathwaycom-pathway)
pw.io.http.rest_connector(
    host="0.0.0.0",
    port=8080,
    schema=IncidentSchema,
    route="/incidents"
)

# Interface queries (in this repo)
response = requests.get("http://backend:8080/incidents")
incidents = response.json()
```

### Option 3: Shared Database (Production)

```python
# Backend writes (in pathwaycom-pathway)
pw.io.postgres.write(
    incidents,
    postgres_settings,
    table_name="incidents"
)

# Interface reads (in this repo)
conn = psycopg2.connect(postgres_settings)
cursor = conn.cursor()
cursor.execute("SELECT * FROM incidents WHERE severity >= 4")
incidents = cursor.fetchall()
```

### Option 4: Message Queue (Production)

```python
# Backend publishes (in pathwaycom-pathway)
pw.io.kafka.write(incidents, kafka_settings, topic="incidents")

# Interface subscribes (in this repo)
consumer = KafkaConsumer("incidents")
for message in consumer:
    incident = json.loads(message.value)
    process_incident(incident)
```

**Current implementation uses Option 1 (file-based) for simplicity.**

---

## Why This Architecture Matters

### 1. Separation of Concerns
- **Backend** (pathwaycom-pathway): Real-time processing, agent decisions, automated actions
- **Interface** (this repo): Human oversight, explanations, auditing

### 2. Responsible AI Deployment
- Agents make fast automated decisions
- Humans can acknowledge, override, or escalate
- Full audit trail of all interventions
- LLM explains "why" decisions were made

### 3. Scalability
- Backend scales horizontally (Pathway clusters)
- Interface is stateless (can run multiple instances)
- Shared storage/API decouples the layers

### 4. Compliance & Auditing
- All human overrides logged with timestamp, operator, reason
- Incident history preserved for forensics
- Regulatory compliance (GDPR, SOC 2, etc.)

---

## API Reference

### Query Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard` | GET | Overview statistics |
| `/api/incidents` | GET | Search incidents with filters |
| `/api/incidents/{id}` | GET | Detailed incident info |
| `/api/incidents/{id}/audit` | GET | Audit trail for incident |
| `/api/summaries` | GET | Pre-computed summaries by source |

### Override Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/incidents/{id}/acknowledge` | POST | Mark incident as acknowledged |
| `/api/incidents/{id}/suppress` | POST | Suppress false positive |
| `/api/incidents/{id}/escalate` | POST | Escalate to different team |
| `/api/incidents/{id}/modify-priority` | POST | Change priority level |
| `/api/incidents/{id}/cancel-action` | POST | Cancel planned action |
| `/api/incidents/{id}/force-action` | POST | Force manual action |

### Explanation Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/explain` | POST | Generate LLM explanation |

### History Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/overrides` | GET | List manual overrides with filters |

---

## Production Deployment Considerations

### Security
- Add authentication (JWT, OAuth2, API keys)
- Implement rate limiting
- Use HTTPS (TLS certificates)
- Configure CORS appropriately

### Monitoring
- Add APM (Datadog, New Relic)
- Log all API calls
- Track override patterns
- Alert on anomalous override activity

### High Availability
- Run multiple API instances behind load balancer
- Use Redis for session storage
- Implement circuit breakers for backend calls
- Add request queuing

### Integration
- Connect to actual Pathway backend REST API
- Integrate with PagerDuty, Slack, JIRA
- Add SSO for operator authentication
- Build React/Vue web UI (replace CLI dashboard)

---

## Development

### Run Tests
```bash
# Run unit tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov=llm --cov-report=html

# Test specific module
pytest tests/test_query_incidents.py -v
```

### Manual Testing
```bash
# Test dashboard CLI
python client/dashboard.py overview
python client/dashboard.py recent 24
python client/dashboard.py details <incident-id>

# Test API endpoints
curl http://localhost:8000/api/dashboard
curl http://localhost:8000/api/incidents
curl -X POST http://localhost:8000/api/explain \
  -H "Content-Type: application/json" \
  -d '{"incident_id": "<id>", "explain_reasoning": true}'
```

### Code Style
```bash
black .
ruff check .
mypy .
```

### API Development
The FastAPI server includes automatic interactive documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## License

MIT License - See LICENSE file

---

## Related Repositories

- **Backend (Agentic AI)**: [pathwaycom-pathway](https://github.com/Jayaprakash3704/pathwaycom-pathway) - Real-time streaming, anomaly detection, 5-agent LangGraph system, automated incident response

**How They Connect:**
```
pathwaycom-pathway (Backend)     pathwaycom-llm-app (Interface)
       |                                    |
       | Generates incidents                | Queries & manages
       v                                    v
   incidents.json  ------------------>  REST API + Dashboard
   summaries.json  ------------------>  LLM Explanations
```

---

## References

- **Pathway Docs**: https://pathway.com/docs/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Groq API**: https://console.groq.com/
- **OpenAI API**: https://platform.openai.com/docs/

---

## Questions?

**What data comes in?**  
Incident records from Pathway backend (JSON files, REST API, or database).

**How does it consume Pathway output?**  
Reads from shared storage (demo) or queries Pathway REST connector (production).

**How do humans interact?**  
REST API for overrides, explanations, and queries. CLI dashboard for monitoring.

**Why separate repos?**  
Clean architecture - backend does streaming/agents, interface handles humans.
