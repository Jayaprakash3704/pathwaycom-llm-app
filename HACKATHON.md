# 🏆 Hackathon Submission: Interface Layer

## Part of: Real-Time Agentic Incident Response System

**Track 1: The Agentic AI (Applied GenAI)**

This repository is the **Interface + Human Oversight Layer** for our Track 1 submission.

👉 **For complete hackathon details, see**: [Backend HACKATHON.md](https://github.com/Jayaprakash3704/pathwaycom-pathway/blob/main/HACKATHON.md)

---

## 🎯 This Repository's Role

While the backend ([pathwaycom-pathway](https://github.com/Jayaprakash3704/pathwaycom-pathway)) handles autonomous agent decisions, **this layer ensures Responsible AI**:

### Key Features

1. **Query System**: REST API to access incident data from Pathway backend
2. **Human Oversight**: Acknowledge, override, escalate, or suppress incidents
3. **Explainability**: LLM-powered explanations of agent decisions
4. **Audit Trail**: Complete history of human interventions
5. **Dashboard**: Real-time CLI monitoring of system health

---

## 🏗️ Why This Matters for Track 1

**The Challenge**: Autonomous agents need human oversight to be production-ready.

**Our Solution**: Separate interface layer that provides:
- ✅ **Transparency**: See what agents decided and why
- ✅ **Control**: Override or cancel agent actions
- ✅ **Compliance**: Full audit trail for regulatory requirements
- ✅ **Explainability**: Natural language explanations using LLM

This is what makes our submission **production-grade, not just a demo**.

---

## 🚀 Key Capabilities

### 1. REST API (FastAPI)

```bash
# Get system overview
GET /api/dashboard

# Query incidents with filters
GET /api/incidents?severity_min=4&hours=24

# Get detailed incident info
GET /api/incidents/{id}

# Explain agent decisions (LLM-powered)
POST /api/explain
{
  "incident_id": "INC-123",
  "explain_reasoning": true,
  "explain_actions": true,
  "explain_impact": true
}
```

### 2. Human-in-the-Loop Controls

```bash
# Acknowledge (human reviewed)
POST /api/incidents/{id}/acknowledge

# Suppress false positive
POST /api/incidents/{id}/suppress

# Escalate to different team
POST /api/incidents/{id}/escalate

# Override agent action
POST /api/incidents/{id}/cancel-action

# Force manual action
POST /api/incidents/{id}/force-action
```

### 3. CLI Dashboard

```bash
# System overview
python client/dashboard.py overview
# Output: 3 incidents, 2 critical, affected services

# Recent incidents
python client/dashboard.py recent 24
# Output: Color-coded incident list with severity bars

# Detailed view
python client/dashboard.py details INC-TEST002
# Output: Full incident details, root cause, actions, acknowledgements

# Watch mode (continuous monitoring)
python client/dashboard.py watch 10
# Output: Auto-refreshing dashboard
```

### 4. LLM Explanation Engine

**Input**: Incident data from backend agents

**Output**: Human-readable explanations

```json
{
  "reasoning": "The incident was detected as an anomaly due to a significant spike in error rates from the payment-service. Our monitoring system tracks key performance indicators (KPIs) such as transaction success rates, latency, and error rates in real-time. When the error rate exceeded 30% (3x baseline), the Observer agent flagged this as a critical anomaly...",
  
  "actions": "The Planning agent recommended restarting the service because historical data shows this resolves 85% of similar payment gateway failures within 2 minutes...",
  
  "impact": "This incident affects all user payment operations, with estimated revenue loss of $15,000 per minute. Approximately 40% of payment transactions are failing..."
}
```

---

## 📊 What We Demonstrate

### Responsible AI Principles

1. **Transparency**: Every agent decision is logged and queryable
2. **Human Control**: Operators can intervene at any point
3. **Explainability**: LLM generates natural language explanations
4. **Auditability**: Complete trail for compliance (GDPR, SOC 2)
5. **Oversight**: Dashboard for real-time monitoring

### Production Readiness

- ✅ FastAPI with automatic OpenAPI docs (Swagger)
- ✅ Environment-based configuration (.env)
- ✅ Error handling and validation
- ✅ Structured logging
- ✅ Type hints throughout
- ✅ Modular architecture

---

## 🔬 Technical Highlights

### 1. Flexible Backend Connection

```python
# Demo: File-based storage
storage = IncidentStorage("./storage")
incidents = storage.get_all_incidents()

# Production: REST API
response = requests.get("http://pathway-backend:8080/incidents")
incidents = response.json()

# Production: Database
conn = psycopg2.connect(postgres_settings)
incidents = conn.execute("SELECT * FROM incidents")

# Production: Kafka
consumer = KafkaConsumer("incidents")
for incident in consumer:
    process_incident(incident)
```

### 2. LLM-Powered Explanations

```python
from llm.explanation_generator import ExplanationGenerator

generator = ExplanationGenerator()

explanation = generator.generate_explanation(
    incident_data=incident,
    explain_reasoning=True,
    explain_actions=True,
    explain_impact=True
)

# Uses Groq/OpenAI to convert technical data → human language
```

### 3. Comprehensive Query Service

```python
query_service = IncidentQueryService(storage)

# Dashboard overview
overview = query_service.get_dashboard_overview()

# Search with filters
incidents = query_service.search_incidents(
    source="payment-service",
    severity_min=4,
    anomaly_type="error_spike",
    hours=24
)

# Get related incidents
details = query_service.get_incident_details("INC-123")
```

---

## 🎬 Demo Flow (Interface Layer)

### Step 1: Start API Server
```bash
python main.py
# Server running at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### Step 2: View Dashboard
```bash
python client/dashboard.py overview
```

**Output**:
```
╔════════════════════════════════════════════════════════════╗
║           INCIDENT RESPONSE DASHBOARD                      ║
╚════════════════════════════════════════════════════════════╝

📊 OVERVIEW
  Total Incidents: 3
  Recent (24h): 3
  Critical: 2
  
🎯 PRIORITY DISTRIBUTION
  P1-CRITICAL: 1 ██████████
  P2-HIGH: 1     █████
  P3-MEDIUM: 1   ███

🔥 AFFECTED SERVICES
  auth-service: 5 incidents (1 P1, 2 P2)
  payment-service: 3 incidents (1 P1)
  notification-service: 2 incidents
```

### Step 3: Get Explanation
```bash
curl -X POST http://localhost:8000/api/explain \
  -H "Content-Type: application/json" \
  -d '{"incident_id": "INC-TEST002", "explain_reasoning": true}'
```

**Response**: Human-readable explanation from LLM

### Step 4: Human Override
```bash
curl -X POST http://localhost:8000/api/incidents/INC-TEST002/acknowledge \
  -H "Content-Type: application/json" \
  -d '{"operator": "alice", "reason": "Monitoring resolution"}'
```

**Result**: Incident marked as reviewed, audit trail updated

---

## 🌟 Innovation in This Layer

### 1. **Separation of Concerns**
- Backend = Fast agent decisions
- Interface = Human oversight + explanations
- Clean architectural boundary

### 2. **LLM Dual-Purpose**
- Backend: Agent reasoning/planning (Groq llama-3.3-70b)
- Interface: Human explanations (same LLM)
- Consistent intelligence across layers

### 3. **Multiple Integration Patterns**
- File-based (demo)
- REST API (production)
- Database (production)
- Message queue (production)
- All via same interface

### 4. **Compliance-Ready**
- Every override logged
- Operator identity tracked
- Reason required for actions
- Full audit trail queryable

---

## 📈 Business Value

**For Operations Teams**:
- Reduce alert fatigue (filter false positives)
- Quick incident acknowledgement
- Force manual actions when needed
- Audit trail for post-mortems

**For Compliance Teams**:
- Complete audit history
- Operator accountability
- Regulatory reporting
- Explainable AI decisions

**For Management**:
- Dashboard for system health
- Override patterns analysis
- Team performance metrics
- Business impact visibility

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Framework** | FastAPI | REST endpoints, auto docs |
| **LLM Integration** | OpenAI SDK | Explanation generation |
| **Storage Interface** | Python dataclasses | Query Pathway outputs |
| **CLI Dashboard** | Rich/Click | Terminal UI |
| **Configuration** | python-dotenv | Environment management |

---

## 📦 What's Included

**API Endpoints** (`app/api.py`):
- 10 REST endpoints
- Automatic OpenAPI documentation
- Request/response validation
- Error handling

**Query System** (`app/query_incidents.py`):
- IncidentStorage interface
- IncidentQueryService business logic
- Multiple backend adapters

**Override System** (`app/manual_override.py`):
- Human-in-the-loop actions
- Audit trail tracking
- Validation logic

**Explanation Engine** (`llm/explanation_generator.py`):
- LLM-powered explanations
- Multiple explanation types
- Error handling

**CLI Dashboard** (`client/dashboard.py`):
- Overview, recent, details commands
- Color-coded output
- Watch mode

---

## 🎯 Track 1 Contribution

This repository demonstrates:

✅ **Production-Ready**: Not just agents, but responsible deployment  
✅ **Human-AI Collaboration**: Best of both worlds  
✅ **Explainable AI**: LLM-powered transparency  
✅ **Compliance**: Audit trails for enterprise use  
✅ **Scalability**: Stateless API, horizontal scaling  

**Together with the backend, we deliver a complete Track 1 solution.**

---

## 📞 Links

**Backend Repository**: https://github.com/Jayaprakash3704/pathwaycom-pathway  
**Full Hackathon Details**: [Backend HACKATHON.md](https://github.com/Jayaprakash3704/pathwaycom-pathway/blob/main/HACKATHON.md)

**This is the interface that makes autonomous agents production-ready.**
