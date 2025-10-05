# Security Best Practices

This document outlines security considerations and best practices for deploying and operating the AI SOC multi-agent framework.

## Table of Contents

- [Secrets Management](#secrets-management)
- [TLS/SSL Configuration](#tlsssl-configuration)
- [Container Security](#container-security)
- [Network Security](#network-security)
- [Database Security](#database-security)
- [Monitoring and Auditing](#monitoring-and-auditing)
- [Incident Response](#incident-response)

## Secrets Management

### Development vs Production

**Development**: The bootstrap script generates secrets locally and stores them in the `secrets/` directory.

**Production**: Use external secrets management:

#### HashiCorp Vault

```bash
# Store secrets in Vault
vault kv put secret/ai-soc/postgres \
  username=aisoc \
  password=<secure-password>

# Retrieve in application
vault kv get -field=password secret/ai-soc/postgres
```

#### AWS Secrets Manager

```bash
# Store secrets
aws secretsmanager create-secret \
  --name ai-soc/postgres-password \
  --secret-string "<secure-password>"

# Retrieve in application
aws secretsmanager get-secret-value \
  --secret-id ai-soc/postgres-password \
  --query SecretString --output text
```

#### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-soc-secrets
type: Opaque
data:
  postgres-password: <base64-encoded>
  jwt-secret: <base64-encoded>
  api-key: <base64-encoded>
```

### Secret Rotation

Rotate secrets every 90 days minimum:

```bash
# Generate new secrets
openssl rand -base64 32 > secrets/db_password_new.txt
openssl rand -base64 64 > secrets/jwt_secret_new.txt

# Update services with zero-downtime rotation
# 1. Update database to accept both old and new passwords
# 2. Update applications to use new credentials
# 3. Revoke old credentials
```

### Key Management

The master encryption key (`master_key.bin`) should be:

1. **Stored in a Hardware Security Module (HSM)** in production
2. **Never committed to version control**
3. **Rotated annually**
4. **Backed up in an encrypted, offline location**

For production:

```python
# utils/crypto.py - Production configuration
import hvac

def _load_master_key() -> bytes:
    """Load master key from Vault/HSM in production."""
    if os.getenv("ENVIRONMENT") == "production":
        client = hvac.Client(url=os.getenv("VAULT_ADDR"))
        client.token = os.getenv("VAULT_TOKEN")
        secret = client.secrets.kv.v2.read_secret_version(
            path="ai-soc/master-key"
        )
        return base64.b64decode(secret["data"]["data"]["key"])
    else:
        # Development fallback
        return Path("/run/secrets/master_key.bin").read_bytes()
```

## TLS/SSL Configuration

### Certificate Management

#### Development

Bootstrap script generates self-signed certificates suitable for local development.

#### Production

Use certificates from a trusted Certificate Authority:

```bash
# Let's Encrypt with Certbot
certbot certonly --standalone \
  -d ai-soc.yourdomain.com \
  --email security@yourdomain.com

# Copy to certs directory
cp /etc/letsencrypt/live/ai-soc.yourdomain.com/fullchain.pem certs/server-cert.pem
cp /etc/letsencrypt/live/ai-soc.yourdomain.com/privkey.pem certs/server-key.pem
```

#### Certificate Pinning

For internal service-to-service communication:

```python
import ssl
import certifi

context = ssl.create_default_context(cafile="certs/ca-cert.pem")
context.check_hostname = True
context.verify_mode = ssl.CERT_REQUIRED
```

### Mutual TLS (mTLS)

Enable mTLS for service-to-service authentication:

```yaml
# docker-compose.yml additions
environment:
  - TLS_ENABLED=true
  - TLS_VERIFY_CLIENT=require
  - TLS_CLIENT_CA=/app/certs/ca-cert.pem
```

## Container Security

### Image Scanning

Scan images regularly for vulnerabilities:

```bash
# Using Trivy
trivy image ai-soc:latest

# Using Docker Scout
docker scout cves ai-soc:latest

# Using Snyk
snyk container test ai-soc:latest
```

### Minimal Base Images

Use minimal base images to reduce attack surface:

```dockerfile
# Good: Alpine-based
FROM python:3.11-alpine

# Better: Distroless
FROM gcr.io/distroless/python3

# Best: Scratch (for compiled binaries)
FROM scratch
```

### Read-Only Root Filesystem

```yaml
services:
  ai-soc:
    read_only: true
    tmpfs:
      - /tmp
      - /run
```

### Drop Capabilities

```yaml
services:
  ai-soc:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

### Security Scanning

Set up automated scanning in CI/CD:

```yaml
# .github/workflows/security-scan.yml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'ai-soc:${{ github.sha }}'
    format: 'sarif'
    output: 'trivy-results.sarif'
```

## Network Security

### Network Segmentation

Create separate networks for different service tiers:

```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true
  data:
    driver: bridge
    internal: true
```

### Firewall Rules

Implement host-level firewall rules:

```bash
# UFW (Ubuntu)
ufw default deny incoming
ufw default allow outgoing
ufw allow 8000/tcp  # Frontend
ufw allow 9000/tcp  # AI SOC API
ufw enable

# iptables
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
iptables -A INPUT -p tcp --dport 9000 -j ACCEPT
iptables -A INPUT -j DROP
```

### Rate Limiting

Implement rate limiting at the API gateway:

```nginx
# nginx.conf
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    proxy_pass http://ai-soc:9000/;
}
```

## Database Security

### Encryption at Rest

Enable database encryption:

```yaml
postgres:
  environment:
    POSTGRES_INITDB_ARGS: "-E UTF8 --data-checksums"
  volumes:
    - type: volume
      source: postgres_data
      target: /var/lib/postgresql/data
      volume:
        driver_opts:
          type: "tmpfs"
          device: "tmpfs"
          o: "encryption=aes-256-gcm"
```

### Connection Security

Enforce SSL/TLS for database connections:

```yaml
postgres:
  command: >
    postgres
    -c ssl=on
    -c ssl_cert_file=/var/lib/postgresql/server.crt
    -c ssl_key_file=/var/lib/postgresql/server.key
```

### Access Control

Implement least privilege:

```sql
-- Create read-only user for analytics
CREATE USER analytics_reader WITH PASSWORD 'secure-password';
GRANT CONNECT ON DATABASE aisoc TO analytics_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_reader;

-- Create application user with limited permissions
CREATE USER app_user WITH PASSWORD 'secure-password';
GRANT CONNECT ON DATABASE aisoc TO app_user;
GRANT SELECT, INSERT, UPDATE ON specific_tables TO app_user;
```

### Backup Encryption

Encrypt database backups:

```bash
# Backup with encryption
docker exec ai-soc-postgres pg_dump -U aisoc aisoc | \
  openssl enc -aes-256-cbc -salt -pbkdf2 -out backup.sql.enc

# Restore
openssl enc -aes-256-cbc -d -pbkdf2 -in backup.sql.enc | \
  docker exec -i ai-soc-postgres psql -U aisoc -d aisoc
```

## Monitoring and Auditing

### Audit Logging

Enable comprehensive audit logging:

```yaml
services:
  ai-soc:
    environment:
      AUDIT_LOG_ENABLED: "true"
      AUDIT_LOG_LEVEL: "INFO"
    volumes:
      - ./logs/audit:/var/log/audit
```

### Security Events

Monitor for security events:

```python
# ai_soc/middleware/security.py
import structlog

logger = structlog.get_logger(__name__)

async def log_security_event(event_type: str, details: dict):
    """Log security events for SIEM integration."""
    logger.warning(
        "security_event",
        event_type=event_type,
        timestamp=datetime.utcnow().isoformat(),
        **details
    )
```

### Metrics and Alerts

Set up alerts for suspicious activity:

```yaml
# prometheus/alerts.yml
groups:
  - name: security
    interval: 30s
    rules:
      - alert: HighFailedAuthAttempts
        expr: rate(auth_failures_total[5m]) > 10
        annotations:
          summary: "High number of failed authentication attempts"

      - alert: UnauthorizedAccessAttempt
        expr: unauthorized_access_total > 0
        annotations:
          summary: "Unauthorized access attempt detected"
```

### Log Forwarding

Forward logs to SIEM:

```yaml
services:
  fluentd:
    image: fluent/fluentd:latest
    volumes:
      - ./fluentd/fluent.conf:/fluentd/etc/fluent.conf
      - ./logs:/var/log/app
    depends_on:
      - ai-soc
```

## Incident Response

### Response Plan

1. **Detect**: Monitor alerts and logs
2. **Contain**: Isolate affected services
3. **Eradicate**: Remove threat
4. **Recover**: Restore services
5. **Lessons Learned**: Update procedures

### Emergency Commands

```bash
# Stop compromised service immediately
docker-compose stop ai-soc

# Isolate container network
docker network disconnect ai-soc-network ai-soc-service

# Capture container state for forensics
docker commit ai-soc-service forensic-snapshot

# Review recent logs
docker logs ai-soc-service --since 1h > incident-logs.txt

# Rotate secrets
./scripts/bootstrap.sh --rotate-secrets

# Restore from backup
docker-compose down ai-soc
docker volume rm ai-soc_postgres_data
# Restore volume from backup
docker-compose up -d
```

### Contact Information

Maintain up-to-date security contact information:

```yaml
# security-contacts.yml
security_team:
  email: security@yourdomain.com
  pagerduty: https://yourdomain.pagerduty.com
  slack: #security-incidents

escalation:
  - level: 1
    contact: on-call-engineer@yourdomain.com
    response_time: 15min
  - level: 2
    contact: security-lead@yourdomain.com
    response_time: 1h
  - level: 3
    contact: ciso@yourdomain.com
    response_time: 4h
```

## Compliance Considerations

### GDPR

- Implement data retention policies
- Support data deletion requests
- Encrypt personal data
- Maintain audit trail

### SOC 2

- Enable audit logging
- Implement access controls
- Regular security assessments
- Incident response procedures

### HIPAA (if applicable)

- Encrypt data in transit and at rest
- Implement BAA with cloud providers
- Regular security risk assessments
- Access logging and monitoring

## Security Checklist

Before deploying to production:

- [ ] Replace all default credentials
- [ ] Enable TLS/SSL for all services
- [ ] Implement mTLS for service communication
- [ ] Set up external secrets management (Vault, AWS Secrets Manager)
- [ ] Enable audit logging
- [ ] Configure log forwarding to SIEM
- [ ] Implement rate limiting
- [ ] Set up security monitoring and alerts
- [ ] Perform vulnerability scanning
- [ ] Enable database encryption at rest
- [ ] Implement network segmentation
- [ ] Configure backup and disaster recovery
- [ ] Document incident response procedures
- [ ] Perform security testing (penetration test)
- [ ] Review and approve security configurations

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)

---

**Last Updated**: Generated with bootstrap deployment implementation
**Version**: 0.1.0
