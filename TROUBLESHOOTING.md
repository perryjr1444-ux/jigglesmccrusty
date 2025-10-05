# Troubleshooting Guide

This guide helps diagnose and resolve common issues with the AI SOC multi-agent framework.

## Table of Contents

- [Pre-Deployment Issues](#pre-deployment-issues)
- [Service Start Issues](#service-start-issues)
- [Connection Issues](#connection-issues)
- [Performance Issues](#performance-issues)
- [Data Issues](#data-issues)
- [Security Issues](#security-issues)

## Pre-Deployment Issues

### Bootstrap Script Fails

**Symptom**: `./scripts/bootstrap.sh` exits with errors

**Possible Causes**:
1. Missing OpenSSL
2. Insufficient permissions
3. Disk space full

**Solutions**:

```bash
# Check OpenSSL installation
openssl version

# Install OpenSSL if missing (macOS)
brew install openssl

# Install OpenSSL if missing (Ubuntu)
sudo apt-get install openssl

# Check disk space
df -h

# Check permissions
chmod +x scripts/bootstrap.sh
```

### Certificate Generation Fails

**Symptom**: Certificate files not created in `certs/` directory

**Solution**:

```bash
# Remove existing partial certificates
rm -rf certs/

# Re-run bootstrap
./scripts/bootstrap.sh

# Verify certificate validity
openssl x509 -in certs/server-cert.pem -text -noout
openssl verify -CAfile certs/ca-cert.pem certs/server-cert.pem
```

## Service Start Issues

### Docker Daemon Not Running

**Symptom**: `Cannot connect to the Docker daemon`

**Solutions**:

```bash
# macOS with Colima
colima status
colima start --cpu 4 --memory 8

# Linux
sudo systemctl status docker
sudo systemctl start docker

# Check Docker is accessible
docker ps
```

### Port Already in Use

**Symptom**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution**:

```bash
# Find process using the port
lsof -i :8000
netstat -tuln | grep 8000

# Kill the process (if safe)
kill -9 <PID>

# Or change ports in docker-compose.yml
# Edit ports section for affected service
ports:
  - "8001:8000"  # Changed from 8000:8000
```

### Services Fail to Start

**Symptom**: Container exits immediately or crashes

**Diagnosis**:

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs <service-name>

# Inspect container
docker inspect ai-soc-service

# Check container events
docker events --filter 'container=ai-soc-service'
```

**Common Solutions**:

```bash
# Rebuild images
docker-compose build --no-cache

# Remove and recreate volumes
docker-compose down -v
./scripts/bootstrap.sh
docker-compose up -d

# Check resource limits
docker stats
```

### PostgreSQL Won't Start

**Symptom**: PostgreSQL container exits or fails health checks

**Solutions**:

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Common issues and fixes:

# 1. Permission issues
docker-compose down
sudo chown -R 999:999 data/postgres/
docker-compose up -d postgres

# 2. Corrupted data directory
docker-compose down
docker volume rm ai-soc_postgres_data
docker-compose up -d postgres
./scripts/bootstrap.sh --init-services

# 3. Port conflict
# Edit docker-compose.yml
ports:
  - "5433:5432"  # Changed from 5432:5432
```

### Kafka Won't Start

**Symptom**: Kafka fails to connect to Zookeeper

**Solutions**:

```bash
# Check Zookeeper is running
docker-compose ps zookeeper
docker-compose logs zookeeper

# Restart Kafka and Zookeeper
docker-compose restart zookeeper kafka

# If still failing, recreate
docker-compose down
docker volume rm ai-soc_kafka_data ai-soc_zookeeper_data
docker-compose up -d zookeeper
sleep 10
docker-compose up -d kafka
```

## Connection Issues

### AI SOC Service Not Responding

**Symptom**: `curl http://localhost:9000/health` fails or times out

**Diagnosis**:

```bash
# Check if container is running
docker ps | grep ai-soc

# Check logs
docker-compose logs ai-soc

# Check network connectivity
docker exec ai-soc-service ping -c 3 postgres
docker exec ai-soc-service curl http://localhost:9000/health
```

**Solutions**:

```bash
# Restart service
docker-compose restart ai-soc

# Check dependencies
docker-compose ps postgres redis kafka

# Verify .env configuration
cat .env | grep -E "DATABASE_URL|REDIS_URL|KAFKA"

# Test database connection
docker exec -it ai-soc-postgres psql -U aisoc -d aisoc -c "SELECT 1;"
```

### Frontend Can't Connect to AI SOC

**Symptom**: Frontend shows connection errors

**Solutions**:

```bash
# Check network connectivity
docker exec ai-soc-frontend curl http://ai-soc:9000/health

# Verify nginx configuration
docker exec ai-soc-frontend cat /etc/nginx/conf.d/default.conf

# Check service discovery
docker exec ai-soc-frontend nslookup ai-soc

# Restart frontend
docker-compose restart frontend
```

### Database Connection Fails

**Symptom**: AI SOC logs show database connection errors

**Solutions**:

```bash
# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Test connection manually
docker exec -it ai-soc-postgres psql -U aisoc -d aisoc

# Check PostgreSQL is accepting connections
docker exec ai-soc-postgres pg_isready -U aisoc

# Verify password
cat secrets/db_password.txt
```

### Kafka Connection Issues

**Symptom**: AI SOC can't connect to Kafka

**Solutions**:

```bash
# Check Kafka is accessible
docker exec ai-soc-kafka kafka-broker-api-versions.sh \
  --bootstrap-server localhost:9092

# List topics
docker exec ai-soc-kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 --list

# Test from AI SOC container
docker exec ai-soc-service nc -zv kafka 9092

# Verify KAFKA_BOOTSTRAP_SERVERS in .env
cat .env | grep KAFKA_BOOTSTRAP_SERVERS
```

## Performance Issues

### Slow Response Times

**Symptom**: API requests take >5 seconds

**Diagnosis**:

```bash
# Check resource usage
docker stats

# Check system resources
top
free -h
df -h

# Check database performance
docker exec -it ai-soc-postgres psql -U aisoc -d aisoc -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '5 seconds';
"
```

**Solutions**:

```bash
# Increase Docker resources (macOS with Colima)
colima stop
colima start --cpu 6 --memory 12

# Add database indexes
docker exec -it ai-soc-postgres psql -U aisoc -d aisoc -c "
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at DESC);
"

# Clear logs to free space
docker-compose logs --no-log-prefix ai-soc > /tmp/backup-logs.txt
docker-compose restart ai-soc
```

### High Memory Usage

**Symptom**: Services consuming excessive memory

**Solutions**:

```bash
# Check current usage
docker stats --no-stream

# Set memory limits in docker-compose.yml
services:
  ai-soc:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

# Restart with limits
docker-compose down
docker-compose up -d
```

### Kafka Lag

**Symptom**: Events not processed in real-time

**Solutions**:

```bash
# Check consumer lag
docker exec ai-soc-kafka kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group ai-soc

# Increase consumer instances or partitions
docker exec ai-soc-kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --alter --topic rbp.metrics \
  --partitions 6

# Scale AI SOC consumers
docker-compose up -d --scale ai-soc=3
```

## Data Issues

### Missing Kafka Topics

**Symptom**: Events not being received

**Solution**:

```bash
# List existing topics
docker exec ai-soc-kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 --list

# Recreate topics
./scripts/bootstrap.sh --init-services

# Or create manually
docker exec ai-soc-kafka kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --create --topic rbp.metrics \
  --partitions 3 --replication-factor 1
```

### Database Schema Mismatch

**Symptom**: SQL errors about missing tables or columns

**Solutions**:

```bash
# Reinitialize schema
./scripts/bootstrap.sh --init-services

# Or manually
docker exec -it ai-soc-postgres psql -U aisoc -d aisoc -f /path/to/schema.sql

# Verify tables exist
docker exec -it ai-soc-postgres psql -U aisoc -d aisoc -c "\dt"
```

### Lost Data After Restart

**Symptom**: Data disappears after restart

**Cause**: Volumes not properly configured

**Solution**:

```bash
# Check volumes
docker volume ls | grep ai-soc

# Verify volume mounts
docker inspect ai-soc-postgres | grep -A 10 Mounts

# Backup data before troubleshooting
docker run --rm -v ai-soc_postgres_data:/data -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres-backup.tar.gz /data
```

## Security Issues

### TLS/SSL Errors

**Symptom**: Certificate verification failures

**Solutions**:

```bash
# Regenerate certificates
rm -rf certs/
./scripts/bootstrap.sh

# Verify certificate chain
openssl verify -CAfile certs/ca-cert.pem certs/server-cert.pem

# Check certificate expiration
openssl x509 -in certs/server-cert.pem -noout -dates

# Test TLS connection
openssl s_client -connect localhost:9000 -CAfile certs/ca-cert.pem
```

### Authentication Failures

**Symptom**: API returns 401 Unauthorized

**Solutions**:

```bash
# Verify API key
cat secrets/api_key.txt

# Check JWT secret
cat secrets/jwt_secret.txt

# Rotate secrets if compromised
./scripts/bootstrap.sh --rotate-secrets
docker-compose restart
```

### Permission Denied Errors

**Symptom**: Services can't read secrets or certificates

**Solutions**:

```bash
# Fix permissions
chmod 700 secrets/
chmod 600 secrets/*
chmod 644 certs/*.pem
chmod 600 certs/*-key.pem

# Check file ownership
ls -la secrets/ certs/

# Fix ownership if needed
sudo chown -R $USER:$USER secrets/ certs/
```

## Emergency Recovery

### Complete Reset

If all else fails, perform a complete reset:

```bash
# WARNING: This will delete all data!

# Stop all services
docker-compose down -v

# Remove generated files
rm -rf secrets/ certs/ data/ .env

# Clean Docker
docker system prune -af --volumes

# Start fresh
./scripts/bootstrap.sh
docker-compose up -d
./scripts/bootstrap.sh --init-services

# Verify
make health
```

### Restore from Backup

```bash
# Stop services
docker-compose down

# Restore PostgreSQL
docker volume rm ai-soc_postgres_data
docker volume create ai-soc_postgres_data
docker run --rm -v ai-soc_postgres_data:/data -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/postgres-backup.tar.gz -C /

# Restore MinIO
docker volume rm ai-soc_minio_data
docker volume create ai-soc_minio_data
docker run --rm -v ai-soc_minio_data:/data -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/minio-backup.tar.gz -C /

# Restart services
docker-compose up -d
```

## Getting Help

If you're still experiencing issues:

1. **Check logs**: `docker-compose logs -f`
2. **Search existing issues**: [GitHub Issues](https://github.com/perryjr1444-ux/jigglesmccrusty/issues)
3. **Create a new issue** with:
   - Output of `docker-compose ps`
   - Relevant logs from `docker-compose logs <service>`
   - Steps to reproduce
   - Environment details (OS, Docker version, etc.)

## Useful Commands

```bash
# Quick health check
make health

# View all logs
make logs

# Check service status
make status

# Restart specific service
docker-compose restart <service-name>

# View container resource usage
docker stats

# Inspect container
docker inspect <container-name>

# Execute command in container
docker exec -it <container-name> bash

# Clean up unused resources
docker system prune -a
```

---

**Last Updated**: Generated with bootstrap deployment implementation
**Version**: 0.1.0
