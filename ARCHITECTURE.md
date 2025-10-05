# Architecture Overview

This document provides a detailed architectural overview of the AI SOC multi-agent framework deployment.

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         External Layer                                    │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐             │
│  │   Browser    │     │  CI/CD       │     │  Monitoring  │             │
│  │   Clients    │     │  Pipeline    │     │  Tools       │             │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘             │
└─────────┼──────────────────────┼─────────────────────┼───────────────────┘
          │                      │                     │
          │                      │                     │
┌─────────▼──────────────────────▼─────────────────────▼───────────────────┐
│                        Application Layer                                  │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    Frontend (Nginx + React)                        │  │
│  │                         Port: 8000                                 │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │  │
│  │  │  Static UI   │  │  API Gateway │  │  Reverse     │            │  │
│  │  │  (React App) │  │  (Nginx)     │  │  Proxy       │            │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │  │
│  └─────────────────────────┬──────────────────────────────────────────┘  │
│                            │                                              │
│  ┌─────────────────────────▼──────────────────────────────────────────┐  │
│  │                 AI SOC Service (FastAPI)                           │  │
│  │                         Port: 9000                                 │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │  │
│  │  │  REST API    │  │  Alert       │  │  Telemetry   │            │  │
│  │  │  Endpoints   │  │  Orchestrator│  │  Processing  │            │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │  │
│  │  │  LLM         │  │  Quota       │  │  Remediation │            │  │
│  │  │  Integration │  │  Publisher   │  │  Generator   │            │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘            │  │
│  └───────┬────────────────┬─────────────────┬────────────────────────┘  │
└──────────┼────────────────┼─────────────────┼───────────────────────────┘
           │                │                 │
           │                │                 │
┌──────────▼────────────────▼─────────────────▼───────────────────────────┐
│                         Data Layer                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  PostgreSQL  │  │    Redis     │  │    Kafka     │  │   MinIO     │ │
│  │  Port: 5432  │  │  Port: 6379  │  │  Port: 9092  │  │ Port: 9000  │ │
│  │              │  │              │  │              │  │             │ │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌─────────┐ │ │
│  │ │ Alerts   │ │  │ │ Cache    │ │  │ │ Topics:  │ │  │ │ Buckets │ │ │
│  │ │ Telemetry│ │  │ │ Sessions │ │  │ │ • rbp.*  │ │  │ │ Models  │ │ │
│  │ │ Quotas   │ │  │ │ Queue    │ │  │ │ • red-*  │ │  │ │ Artifacts│ │ │
│  │ └──────────┘ │  │ └──────────┘ │  │ │ • blue-* │ │  │ └─────────┘ │ │
│  └──────────────┘  └──────────────┘  │ │ • purple*│ │  └─────────────┘ │
│                                       │ └──────────┘ │                   │
│  ┌──────────────┐  ┌──────────────┐  └──────────────┘                   │
│  │ Vault (Dev)  │  │  Zookeeper   │                                      │
│  │  Port: 8200  │  │  Port: 2181  │                                      │
│  └──────────────┘  └──────────────┘                                      │
└───────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### Frontend Layer

**Container**: `ai-soc-frontend`  
**Image**: Custom Nginx + React build  
**Responsibilities**:
- Serve static React application
- API gateway and reverse proxy
- Route `/api/ai-soc/*` to AI SOC service
- Handle CORS and security headers

**Key Features**:
- Health check endpoint at `/health`
- Optimized static asset serving
- Request routing and load balancing

### AI SOC Service

**Container**: `ai-soc-service`  
**Image**: Python 3.11 + FastAPI  
**Port**: 9000  
**Responsibilities**:
- Process telemetry events
- Generate and manage security alerts
- Integrate with LLM for threat analysis
- Publish quota updates
- Generate remediation playbooks

**API Endpoints**:
- `GET /health` - Health check
- `POST /telemetry` - Ingest telemetry events
- `GET /alerts` - List alerts with pagination
- `GET /alerts/{alert_id}` - Get specific alert

**Dependencies**:
- PostgreSQL (storage)
- Redis (cache/queue)
- Kafka (event streaming)

### PostgreSQL

**Container**: `ai-soc-postgres`  
**Port**: 5432  
**Schema**:

```sql
-- Alerts table
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(64) UNIQUE NOT NULL,
    severity VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    remediation TEXT,
    status VARCHAR(20) DEFAULT 'open',
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Telemetry events table
CREATE TABLE telemetry_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(64) UNIQUE NOT NULL,
    source VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quota updates table
CREATE TABLE quota_updates (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    reason TEXT,
    self_suggest_enabled BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Redis

**Container**: `ai-soc-redis`  
**Port**: 6379  
**Use Cases**:
- Session caching
- Rate limiting
- Temporary data storage
- Pub/Sub messaging

### Kafka

**Container**: `ai-soc-kafka`  
**Port**: 9092 (internal), 29092 (external)  
**Topics**:
- `rbp.metrics` - Device/agent metrics
- `rbp.proposals` - Proposed changes
- `rbp.approvals` - Approved changes
- `rbp.alerts` - Security alerts
- `rbp.quota_updates` - Quota manager updates
- `red-scenarios` - Red team scenarios
- `blue-responses` - Blue team responses
- `purple-gaps` - Purple team gap analysis

**Configuration**:
- Single broker (development)
- 3 partitions per topic
- Auto-create topics enabled

### MinIO

**Container**: `ai-soc-minio`  
**Ports**: 9000 (API), 9001 (Console)  
**Buckets**:
- `ai-soc-artifacts` - General artifacts
- `ai-soc-models` - ML model storage

**Use Cases**:
- Store large artifacts
- Model versioning
- Backup storage

### Vault (Development)

**Container**: `ai-soc-vault`  
**Port**: 8200  
**Mode**: Development (not for production)  
**Purpose**: Secrets management demonstration

**Production Alternative**: Use external Vault cluster or cloud secrets manager

## Network Architecture

**Network**: `ai-soc-network`  
**Type**: Bridge  
**Subnet**: 172.28.0.0/16

### Service Communication

```
Frontend (8000)
    ↓ HTTP
AI SOC Service (9000)
    ↓ PostgreSQL Protocol
PostgreSQL (5432)
    
AI SOC Service (9000)
    ↓ Redis Protocol
Redis (6379)

AI SOC Service (9000)
    ↓ Kafka Protocol
Kafka (9092) ← Zookeeper (2181)

AI SOC Service (9000)
    ↓ S3 API
MinIO (9000)

AI SOC Service (9000)
    ↓ HTTP/HTTPS
Vault (8200)
```

## Data Flow

### 1. Telemetry Ingestion

```
Device/Agent
    → Kafka (rbp.metrics)
        → AI SOC Consumer
            → Process & Correlate
                → Generate Alert (if needed)
                    → PostgreSQL (store)
                    → Kafka (rbp.alerts)
```

### 2. Alert Processing

```
Telemetry Event
    → AI SOC Service
        → LLM Analysis (optional)
            → Generate Remediation
                → Store in PostgreSQL
                    → Notify Review Board
                        → Quota Update (if approved)
                            → Kafka (rbp.quota_updates)
```

### 3. User Workflow

```
User Browser
    → Frontend (React)
        → API Request
            → Nginx Proxy
                → AI SOC Service
                    → Query PostgreSQL
                        → Return Results
                            → Display in UI
```

## Security Architecture

### Authentication & Authorization

```
Request
    → API Gateway (Frontend)
        → JWT Validation
            → API Key Check
                → AI SOC Service
                    → Role-Based Access
                        → Resource Access
```

### Encryption

**In Transit**:
- TLS 1.3 for all HTTP communications
- PostgreSQL SSL connections
- Kafka SSL/SASL (production)

**At Rest**:
- PostgreSQL encryption (optional)
- MinIO server-side encryption
- Encrypted volumes (production)

### Secrets Management

**Development**:
- Local files in `secrets/` directory
- Environment variables in `.env`
- Volume-mounted secrets

**Production**:
- External Vault cluster
- Cloud secrets managers (AWS Secrets Manager, Azure Key Vault)
- Kubernetes secrets

## Scalability

### Horizontal Scaling

**AI SOC Service**:
```bash
# Scale to 3 instances
docker-compose up -d --scale ai-soc=3
```

**Kafka Consumers**:
- Multiple consumer instances in same group
- Partition-based load distribution

### Vertical Scaling

```yaml
services:
  ai-soc:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

### Load Balancing

**Nginx Configuration**:
```nginx
upstream ai_soc_backend {
    server ai-soc-1:9000;
    server ai-soc-2:9000;
    server ai-soc-3:9000;
}
```

## High Availability

### Database Replication

```yaml
# Primary-Replica setup
postgres-primary:
  image: postgres:16-alpine
  environment:
    POSTGRES_REPLICATION: "true"

postgres-replica:
  image: postgres:16-alpine
  environment:
    POSTGRES_PRIMARY_HOST: postgres-primary
```

### Service Health Checks

All services include health checks:
- FastAPI: `GET /health`
- PostgreSQL: `pg_isready`
- Redis: `redis-cli ping`
- Kafka: `kafka-broker-api-versions`

### Backup Strategy

**Automated Backups**:
```bash
# Daily PostgreSQL backup
0 2 * * * /path/to/backup-postgres.sh

# Weekly MinIO backup
0 3 * * 0 /path/to/backup-minio.sh
```

## Monitoring & Observability

### Metrics Collection

**Prometheus** (optional):
- Application metrics (FastAPI)
- Container metrics (cAdvisor)
- System metrics (Node Exporter)

### Logging

**Structured Logging** (JSON):
```python
import structlog

logger = structlog.get_logger()
logger.info("event", 
    event_type="alert_created",
    alert_id="...",
    severity="high")
```

**Log Aggregation**:
- Docker logs → Fluentd → Elasticsearch → Kibana
- Or: Docker logs → CloudWatch/Stackdriver

### Tracing

**Distributed Tracing** (OpenTelemetry):
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("process_telemetry"):
    # Process event
    pass
```

## Deployment Models

### Local Development

```bash
./scripts/quick-start.sh
```

**Characteristics**:
- Single host
- Development secrets
- All services on one machine
- Suitable for: Development, testing, demos

### Staging/Testing

```bash
# With production-like configuration
export ENVIRONMENT=staging
./scripts/bootstrap.sh
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

**Characteristics**:
- Production-like setup
- External secrets management
- SSL/TLS enabled
- Suitable for: Integration testing, UAT

### Production

**Kubernetes Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-soc
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: ai-soc
        image: ai-soc:latest
        envFrom:
        - secretRef:
            name: ai-soc-secrets
```

**Characteristics**:
- Multi-node cluster
- External managed services
- Full SSL/mTLS
- High availability
- Automated scaling
- Suitable for: Production workloads

## Performance Considerations

### Database Optimization

**Indexes**:
```sql
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_status ON alerts(status);
CREATE INDEX idx_alerts_created ON alerts(created_at DESC);
CREATE INDEX idx_telemetry_source ON telemetry_events(source);
```

**Connection Pooling**:
```python
# SQLAlchemy configuration
pool_size=20
max_overflow=10
pool_pre_ping=True
```

### Caching Strategy

**Redis Caching**:
```python
# Cache frequently accessed data
cache.set(f"alert:{alert_id}", alert_data, ttl=300)
```

### Kafka Optimization

**Producer Configuration**:
```python
producer_config = {
    'batch.size': 16384,
    'linger.ms': 10,
    'compression.type': 'lz4'
}
```

## Disaster Recovery

### Backup Schedule

- PostgreSQL: Daily full backup, hourly incremental
- MinIO: Daily backup
- Configuration: Version controlled in Git

### Recovery Procedures

```bash
# 1. Restore PostgreSQL
cat backup.sql | docker exec -i ai-soc-postgres psql -U aisoc -d aisoc

# 2. Restore MinIO
tar xzf minio-backup.tar.gz -C /path/to/minio/data

# 3. Restart services
docker-compose up -d
```

### RTO/RPO Targets

- **Recovery Time Objective (RTO)**: < 1 hour
- **Recovery Point Objective (RPO)**: < 15 minutes

---

**Version**: 0.1.0  
**Last Updated**: Generated with bootstrap deployment implementation
