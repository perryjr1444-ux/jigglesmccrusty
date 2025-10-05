# AI SOC Deployment Guide

This guide provides comprehensive instructions for deploying the AI-Powered Security Operations Center (AI SOC) multi-agent framework using Docker and Docker Compose.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Manual Deployment](#manual-deployment)
- [CI/CD Deployment](#cicd-deployment)
- [Configuration](#configuration)
- [Service Architecture](#service-architecture)
- [Troubleshooting](#troubleshooting)
- [Security Best Practices](#security-best-practices)

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows with WSL2
- **Docker**: Version 24.0 or later
- **Docker Compose**: Version 2.20 or later
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Disk Space**: Minimum 20GB free space
- **CPU**: 4+ cores recommended

### macOS-Specific Setup

```bash
# Install Colima and Docker
brew install colima docker docker-compose

# Start Colima with adequate resources
colima start --cpu 4 --memory 8 --disk 50
```

### Linux Setup

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

## Quick Start

The fastest way to get started is using our bootstrap script:

```bash
# 1. Clone the repository
git clone https://github.com/perryjr1444-ux/jigglesmccrusty.git
cd jigglesmccrusty

# 2. Run the bootstrap script to generate secrets and certificates
./scripts/bootstrap.sh

# 3. Start all services
docker-compose up -d

# 4. Initialize Kafka topics, MinIO buckets, and database schema
./scripts/bootstrap.sh --init-services

# 5. Verify all services are running
docker-compose ps

# 6. Access the services
# - Frontend/API: http://localhost:8000
# - AI SOC Service: http://localhost:9000
# - MinIO Console: http://localhost:9001
# - Vault UI: http://localhost:8200
```

## Manual Deployment

### Step 1: Generate Secrets and Certificates

The bootstrap script generates:
- Master encryption key (AES-256)
- JWT secret for authentication
- Database passwords
- MinIO access credentials
- Vault root token
- TLS certificates (CA, server)

```bash
./scripts/bootstrap.sh
```

This creates:
- `secrets/` directory with encrypted credentials
- `certs/` directory with TLS certificates
- `.env` file with all configuration

### Step 2: Review Configuration

Inspect the generated `.env` file and adjust if needed:

```bash
cat .env
```

Key configuration items:
- Database connection strings
- Kafka bootstrap servers
- MinIO endpoints
- Service ports
- Log levels

### Step 3: Start Infrastructure Services

Start backing services first (database, cache, message queue):

```bash
# Start PostgreSQL, Redis, Kafka, MinIO, and Vault
docker-compose up -d postgres redis zookeeper kafka minio vault

# Wait for services to be ready
docker-compose ps

# Check logs if any service fails
docker-compose logs postgres
docker-compose logs kafka
```

### Step 4: Initialize Services

Run the initialization script to set up:
- Kafka topics for RBP pipeline
- MinIO buckets for artifacts and models
- Database schema for alerts and telemetry

```bash
./scripts/bootstrap.sh --init-services
```

### Step 5: Start Application Services

```bash
# Start AI SOC microservice and frontend
docker-compose up -d ai-soc frontend

# View logs
docker-compose logs -f ai-soc
docker-compose logs -f frontend
```

### Step 6: Verify Deployment

```bash
# Check all containers are running
docker-compose ps

# Test AI SOC health endpoint
curl http://localhost:9000/health

# Test frontend health endpoint
curl http://localhost:8000/health

# Access the web interface
open http://localhost:8000  # macOS
xdg-open http://localhost:8000  # Linux
```

## CI/CD Deployment

### GitHub Actions Example

```yaml
name: Deploy AI SOC

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Generate secrets (use GitHub Secrets in production)
        run: ./scripts/bootstrap.sh
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Initialize services
        run: ./scripts/bootstrap.sh --init-services
      
      - name: Run health checks
        run: |
          sleep 30
          curl -f http://localhost:9000/health
          curl -f http://localhost:8000/health
      
      - name: Run tests
        run: |
          cd ai_soc
          docker-compose exec -T ai-soc pytest
```

### GitLab CI Example

```yaml
deploy:
  image: docker:latest
  services:
    - docker:dind
  script:
    - apk add --no-cache bash curl openssl
    - ./scripts/bootstrap.sh
    - docker-compose up -d
    - ./scripts/bootstrap.sh --init-services
    - sleep 30
    - curl -f http://localhost:9000/health
```

## Configuration

### Environment Variables

All configuration is managed through environment variables. See `.env.example` for a complete list.

#### Critical Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_PASSWORD` | Database password | Generated |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka brokers | kafka:9092 |
| `MINIO_ROOT_USER` | MinIO access key | Generated |
| `VAULT_TOKEN` | Vault root token | Generated |
| `LOG_LEVEL` | Application log level | INFO |

#### AI SOC Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_SOC_KAFKA_GROUP_ID` | Kafka consumer group | ai-soc |
| `AI_SOC_ALERTS_TOPIC` | Topic for publishing alerts | rbp.alerts |
| `AI_SOC_THREAT_INTEL_FEEDS` | CTI feed URLs | CVE, OTX |
| `AI_SOC_LLM_MODEL` | LLM model identifier | lumo-ai-soc |

### Volume Management

Persistent data is stored in Docker volumes:

```bash
# List volumes
docker volume ls | grep ai-soc

# Backup PostgreSQL data
docker run --rm -v ai-soc_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz /data

# Backup MinIO data
docker run --rm -v ai-soc_minio_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/minio-backup.tar.gz /data

# Remove all volumes (WARNING: data loss)
docker-compose down -v
```

## Service Architecture

### Service Overview

| Service | Container | Port(s) | Purpose |
|---------|-----------|---------|---------|
| PostgreSQL | ai-soc-postgres | 5432 | Primary database |
| Redis | ai-soc-redis | 6379 | Cache and pub/sub |
| Zookeeper | ai-soc-zookeeper | 2181 | Kafka coordination |
| Kafka | ai-soc-kafka | 9092, 29092 | Event streaming |
| MinIO | ai-soc-minio | 9000, 9001 | Object storage |
| Vault | ai-soc-vault | 8200 | Secrets management |
| AI SOC | ai-soc-service | 9000 | Security operations |
| Frontend | ai-soc-frontend | 8000 | Web UI and API gateway |

### Network Architecture

All services communicate on the `ai-soc-network` bridge network (172.28.0.0/16):

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Network                          │
│                    (ai-soc-network)                          │
│                                                               │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │PostgreSQL│    │  Redis   │    │  Kafka   │              │
│  │  :5432   │    │  :6379   │    │  :9092   │              │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘              │
│       │               │               │                      │
│       └───────────────┴───────────────┘                      │
│                       │                                      │
│              ┌────────▼─────────┐                            │
│              │    AI SOC        │                            │
│              │  Service :9000   │                            │
│              └────────┬─────────┘                            │
│                       │                                      │
│              ┌────────▼─────────┐                            │
│              │   Frontend       │                            │
│              │   Nginx :8000    │◄──── External Traffic      │
│              └──────────────────┘                            │
│                                                               │
│  ┌──────────┐    ┌──────────┐                               │
│  │  MinIO   │    │  Vault   │                               │
│  │  :9000   │    │  :8200   │                               │
│  └──────────┘    └──────────┘                               │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Telemetry Ingestion**: Devices/agents → Kafka topics → AI SOC
2. **Alert Processing**: AI SOC → PostgreSQL → Review Board UI
3. **Artifact Storage**: AI SOC → MinIO buckets
4. **Secret Management**: Services → Vault API
5. **User Interface**: Browser → Frontend (Nginx) → AI SOC API

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check Docker daemon
docker info

# Check available resources
docker system df

# View service logs
docker-compose logs <service-name>

# Restart specific service
docker-compose restart <service-name>
```

#### Database Connection Errors

```bash
# Verify PostgreSQL is ready
docker exec ai-soc-postgres pg_isready -U aisoc

# Check database logs
docker-compose logs postgres

# Connect to database manually
docker exec -it ai-soc-postgres psql -U aisoc -d aisoc
```

#### Kafka Connection Issues

```bash
# List Kafka topics
docker exec ai-soc-kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 --list

# Check Kafka logs
docker-compose logs kafka

# Verify Zookeeper is running
docker-compose ps zookeeper
```

#### Certificate Errors

```bash
# Regenerate certificates
rm -rf certs/
./scripts/bootstrap.sh

# Verify certificate validity
openssl x509 -in certs/server-cert.pem -text -noout
```

#### Permission Denied Errors

```bash
# Fix secrets directory permissions
chmod 700 secrets/
chmod 600 secrets/*

# Fix certificate permissions
chmod 644 certs/*.pem
chmod 600 certs/*-key.pem
```

### Health Check Commands

```bash
# AI SOC Service
curl http://localhost:9000/health

# Frontend
curl http://localhost:8000/health

# PostgreSQL
docker exec ai-soc-postgres pg_isready

# Redis
docker exec ai-soc-redis redis-cli ping

# MinIO
curl http://localhost:9000/minio/health/live

# Vault
docker exec ai-soc-vault vault status
```

### Debugging Tips

```bash
# View real-time logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f ai-soc

# Execute commands in running container
docker exec -it ai-soc-service bash

# Check resource usage
docker stats

# Inspect container details
docker inspect ai-soc-service
```

## Security Best Practices

### Production Deployment Checklist

- [ ] **Use external secret management**: Replace dev Vault with production Vault or AWS Secrets Manager
- [ ] **Enable TLS everywhere**: Set `TLS_ENABLED=true` and configure proper certificates
- [ ] **Rotate secrets regularly**: Update database passwords, API keys, and JWT secrets every 90 days
- [ ] **Use read-only containers**: Add `read_only: true` to service definitions
- [ ] **Implement network policies**: Restrict inter-service communication to required paths
- [ ] **Enable audit logging**: Configure centralized logging with ELK or Splunk
- [ ] **Scan images for vulnerabilities**: Use `docker scan` or Trivy before deployment
- [ ] **Set resource limits**: Define CPU and memory limits in docker-compose.yml
- [ ] **Use non-root users**: All services run as non-root users
- [ ] **Backup regularly**: Schedule automated backups of PostgreSQL and MinIO

### Secrets Management

Never commit secrets to version control:

```bash
# Ensure .env and secrets/ are in .gitignore
git status secrets/
git status .env

# Use environment-specific .env files
cp .env .env.production
# Edit .env.production with production values
```

For production, use external secret management:

```bash
# Example: Load from AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id ai-soc/postgres-password \
  --query SecretString --output text

# Example: Load from HashiCorp Vault
vault kv get -field=password secret/ai-soc/postgres
```

### Hardening Recommendations

1. **Run containers read-only** where possible
2. **Use encrypted volumes** for sensitive data (APFS on macOS, LUKS on Linux)
3. **Enable SELinux/AppArmor** profiles
4. **Implement rate limiting** on API endpoints
5. **Use mTLS** for service-to-service communication
6. **Enable database encryption** at rest
7. **Implement RBAC** with Vault policies
8. **Monitor container drift** with security scanning tools
9. **Use image signing** with Docker Content Trust
10. **Implement network segmentation** with firewall rules

### Monitoring

Set up monitoring with Prometheus and Grafana:

```yaml
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana:latest
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=<secure-password>
```

## Additional Resources

- [AI SOC Architecture](README.md#ai-soc-layers-and-how-they-defend-your-devices)
- [Operational Runbook](README.md#operational-runbook)
- [LLM Suite Reference](README.md#llm-suite-reference-architecture)
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Migration Guide](docs/kubernetes.md) (future)

## Support

For issues and questions:
- Open an issue on [GitHub](https://github.com/perryjr1444-ux/jigglesmccrusty/issues)
- Review existing issues and discussions
- Check the troubleshooting section above

---

**Last Updated**: Generated by bootstrap deployment implementation
**Version**: 0.1.0
