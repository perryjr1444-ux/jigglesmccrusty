# Quick Reference Card

Essential commands for working with the AI SOC multi-agent framework.

## Quick Start

```bash
# One-command deployment
./scripts/quick-start.sh

# Or using Make
make deploy
```

## Common Commands

### Starting and Stopping

```bash
make start          # Start all services
make stop           # Stop all services
make restart        # Restart all services
make down           # Stop and remove containers
```

### Monitoring

```bash
make status         # Show service status
make health         # Check service health
make logs           # View all logs
make logs-ai-soc    # View AI SOC logs
make logs-frontend  # View frontend logs
```

### Development

```bash
make dev            # Start in development mode
make build          # Build Docker images
make test           # Run tests
make shell-ai-soc   # Open shell in AI SOC container
```

### Maintenance

```bash
make backup         # Backup databases
make clean          # Remove all data (WARNING!)
```

## Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:8000 | Web UI |
| AI SOC API | http://localhost:9000 | REST API |
| MinIO Console | http://localhost:9001 | Object storage UI |
| Vault UI | http://localhost:8200 | Secrets management |

## Health Check URLs

```bash
curl http://localhost:9000/health    # AI SOC
curl http://localhost:8000/health    # Frontend
```

## Docker Commands

```bash
# View containers
docker-compose ps

# View logs
docker-compose logs -f [service]

# Restart service
docker-compose restart [service]

# Execute command in container
docker exec -it [container] bash

# View resource usage
docker stats
```

## Database Access

```bash
# PostgreSQL
docker exec -it ai-soc-postgres psql -U aisoc -d aisoc

# Redis
docker exec -it ai-soc-redis redis-cli

# Common queries
# List all alerts
SELECT * FROM alerts ORDER BY created_at DESC LIMIT 10;

# Count alerts by severity
SELECT severity, COUNT(*) FROM alerts GROUP BY severity;
```

## Kafka Operations

```bash
# List topics
docker exec ai-soc-kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 --list

# Describe topic
docker exec ai-soc-kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --describe --topic rbp.alerts

# Consume messages
docker exec ai-soc-kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic rbp.alerts --from-beginning
```

## MinIO Operations

```bash
# List buckets
docker exec ai-soc-minio mc ls local/

# Upload file
docker exec ai-soc-minio mc cp /path/to/file local/ai-soc-artifacts/

# Download file
docker exec ai-soc-minio mc cp local/ai-soc-artifacts/file /path/to/destination
```

## Troubleshooting

```bash
# Check service health
make health

# View all logs
make logs

# Restart specific service
docker-compose restart ai-soc

# Complete reset (WARNING: data loss)
make clean
make deploy
```

## API Examples

### Submit Telemetry Event

```bash
curl -X POST http://localhost:9000/telemetry \
  -H "Content-Type: application/json" \
  -d '{
    "source": "device-001",
    "event_type": "suspicious_activity",
    "payload": {
      "activity": "unauthorized_access",
      "severity": "high"
    }
  }'
```

### List Alerts

```bash
# All alerts
curl http://localhost:9000/alerts

# With pagination
curl "http://localhost:9000/alerts?limit=10&cursor=0"
```

### Get Specific Alert

```bash
curl http://localhost:9000/alerts/{alert_id}
```

## Environment Variables

Key variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql://aisoc:password@postgres:5432/aisoc

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# AI SOC
AI_SOC_KAFKA_GROUP_ID=ai-soc
AI_SOC_ALERTS_TOPIC=rbp.alerts

# Logging
LOG_LEVEL=INFO
```

## File Locations

```
jigglesmccrusty/
├── .env                    # Configuration
├── docker-compose.yml      # Service orchestration
├── Dockerfile             # Frontend image
├── Makefile               # Common commands
├── secrets/               # Generated secrets
├── certs/                 # TLS certificates
├── data/                  # Persistent data
├── scripts/
│   ├── bootstrap.sh       # Initialize environment
│   ├── quick-start.sh     # One-command deployment
│   └── demo.sh            # Demo script
└── ai_soc/
    ├── Dockerfile         # AI SOC image
    └── pyproject.toml     # Python dependencies
```

## Security

```bash
# View secrets (development only!)
cat secrets/api_key.txt
cat secrets/jwt_secret.txt

# Regenerate secrets
rm -rf secrets/
./scripts/bootstrap.sh

# Rotate database password
# 1. Generate new password
openssl rand -base64 32 > secrets/db_password_new.txt

# 2. Update PostgreSQL
docker exec -it ai-soc-postgres psql -U aisoc -d aisoc \
  -c "ALTER USER aisoc WITH PASSWORD '$(cat secrets/db_password_new.txt)';"

# 3. Update .env and restart
docker-compose restart
```

## Backup and Restore

```bash
# Backup
make backup

# Manual backup
docker exec ai-soc-postgres pg_dump -U aisoc aisoc > backup.sql

# Restore
cat backup.sql | docker exec -i ai-soc-postgres psql -U aisoc -d aisoc
```

## Performance Tuning

```bash
# Check resource usage
docker stats

# Increase Docker resources (macOS)
colima stop
colima start --cpu 6 --memory 12

# Scale services
docker-compose up -d --scale ai-soc=3

# Add database indexes
docker exec -it ai-soc-postgres psql -U aisoc -d aisoc -c "
CREATE INDEX idx_name ON table_name(column_name);
"
```

## Getting Help

```bash
# Show available Make targets
make help

# View comprehensive documentation
cat DEPLOYMENT.md
cat TROUBLESHOOTING.md
cat SECURITY.md

# Check service logs
docker-compose logs [service]

# GitHub Issues
# https://github.com/perryjr1444-ux/jigglesmccrusty/issues
```

## Demo Workflow

```bash
# 1. Start services
make start

# 2. Run demo
./scripts/demo.sh

# 3. View results
curl http://localhost:9000/alerts

# 4. Access UI
open http://localhost:8000  # macOS
xdg-open http://localhost:8000  # Linux
```

---

**Tip**: Save this file locally and keep it handy for quick reference!

Print version: `make help | less`
