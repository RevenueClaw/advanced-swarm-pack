# Architecture Overview

## System Design

The Advanced Swarm Pack adds enterprise-grade capabilities to OpenClaw through a modular skill architecture.

```
┌─────────────────────────────────────────────────────────────────┐
│                        LEADER NODE                              │
│                   (Radxa Rock 5B, 32GB)                         │
├─────────────┬─────────────┬─────────────┬───────────────────────┤
│             │             │             │                       │
│ Hierarchical│ User Pref   │ Versioning  │ Consensus             │
│ Task        │ Learning    │ Manager     │ Debater               │
│ Orchestrator│             │             │                       │
│             │             │             │                       │
└──────┬──────┴──────┬──────┴──────┬──────┴───────────┬───────────┘
       │             │             │                  │
       └─────────────┴─────────────┴──────────────────┘
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
┌────────────┐   ┌────────────┐   ┌────────────┐
│ GPU Worker │   │ Light      │   │ External   │
│ (Ollama)   │   │ Worker     │   │ Services   │
│            │   │ (Pi 5)     │   │            │
│ CUDA       │   │ Scripts,   │   │ OpenRouter │
│ Inference  │   │ Monitor    │   │ APIs       │
└────────────┘   └────────────┘   └────────────┘
```

## Key Components

### 1. Hierarchical Task Orchestration (`skill-hierarchical-orchestrator`)

- **Supervisor Agent**: Receives high-level goals, decomposes into subtasks
- **Task Queue**: Priority-based work distribution
- **Worker Router**: Assigns tasks to nodes by capability
- **Result Aggregator**: Combines partial results into coherent outputs

### 2. User Preference Learning (`skill-preference-learning`)

```
HITL Feedback → Classification → Pattern Extraction → Trait Storage
                                                    ↓
User Query → Confidence Check → Apply Learned Preference → Execute
```

**Feedback Types:**
- Explicit: "Always do X"
- Correction: "No, that's wrong"
- Confirmation: "Good, thanks"
- Rejection: "That didn't work"

**Trait Storage:**
- JSON atomic persistence
- Confidence decay over time
- Contradiction handling

### 3. Skill Versioning (`skill-versioning`)

**Status Lifecycle:**
```
DEVELOPMENT → SHADOW → STAGING → PRODUCTION → DEPRECATED
                   ↓         ↓              ↓
                   └─────────┴──────────────┘
                              ↓
                         ROLLED_BACK
```

**Shadow Testing:**
- Production version returns result to user
- Shadow version runs invisibly, compares output
- Results logged for analysis
- Minimum 50 successful shadow runs before promotion

### 4. Consensus & Debate (`skill-consensus`)

**Trigger Conditions:**
```python
risk_score >= 0.6 or 
confidence < 0.7 or 
has_rejection_history or 
is_novel
```

**Debate Flow:**
1. Conservative presents risks
2. Innovative presents opportunities
3. Each critiques others
4. Pragmatic synthesizes
5. Final recommendation with caveats

### 5. Resource Awareness (`skill-resource-awareness`)

**Cost Tracking:**
- Per-request token counting
- Model-specific pricing (OpenRouter)
- Daily/monthly budget enforcement
- Auto-fallback threshold

**Backend Selection:**
```
Request Arrives
       ↓
Check Requirements
       ↓
Can Local Handle? → Yes → Route to Ollama
       ↓ No
Priority/Cost/Quality → Route to OpenRouter Model
       ↓
Track Usage & Latency
```

## Data Flow

### Typical Request Flow

1. **User Input** → Leader Node receives request
2. **Preference Check** → Apply learned communication style
3. **Uncertainty Assessment** → Gate to debate if needed
4. **Task Decomposition** → Supervisor breaks into subtasks
5. **Worker Assignment** → Route by capability
6. **Execution** → Worker processes, returns result
7. **Versioning Check** → Shadow test if shadow mode active
8. **Synthesis** → Combine results
9. **Response** → Format per user preferences
10. **Feedback Capture** → Log HITL interaction

### Persistence Guarantees

- **Atomic Writes**: All state changes use temp file + rename
- **JSONL Logs**: Append-only for audit trails
- **Validation**: Schema checks on load

## Security Model

- **Node Authentication**: Pairing codes, TLS
- **Credential Isolation**: Per-node credential storage
- **Least Privilege**: Tasks run with minimal required permissions
- **Audit Logging**: All external actions logged

## Performance Characteristics

| Component | Latency | Throughput | Memory |
|-----------|---------|------------|--------|
| Task Orchestration | 50-200ms | 10 req/sec | 100MB |
| Preference Lookup | 1-5ms | 1000 req/sec | 50MB |
| Versioning | 10-20ms | 100 req/sec | 20MB |
| Consensus | 5-30s | 2 debates/min | Minimal |
| Cost Tracking | 1ms | 10000 req/sec | 10MB |

## Failure Modes

1. **Worker Node Failure** → Task rerouted to capable standby
2. **Leader Node Failure** → Manual recovery, pending HA design
3. **Model API Failure** → Fallback to local or retry
4. **Network Partition** → Node marked disconnected, tasks queued
5. **Budget Exhaustion** → Hard stop, admin notification

## Future Directions

- **Leader HA**: Active-passive clustering
- **GPU Scheduling**: Dynamic load-based routing
- **Auto-Scaling**: Spin up cloud workers on demand
- **Web Dashboard**: Real-time swarm visualization
