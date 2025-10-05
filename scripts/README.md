# Scripts Directory

This directory contains utility scripts for bootstrapping, deploying, and managing the AI SOC multi-agent framework.

## Available Scripts

### bootstrap.sh

Main bootstrap script that initializes the environment.

**Usage**:
```bash
# Initial setup - generates secrets, certificates, and .env file
./scripts/bootstrap.sh

# Initialize services after docker-compose up
./scripts/bootstrap.sh --init-services
```

**What it does**:
- Creates directory structure (`secrets/`, `certs/`, `data/`)
- Generates secrets (master key, JWT secret, database passwords, API keys)
- Creates TLS certificates (CA and server certificates)
- Generates `.env` configuration file
- Initializes Kafka topics (when run with `--init-services`)
- Creates MinIO buckets (when run with `--init-services`)
- Sets up database schema (when run with `--init-services`)

**Options**:
- `--init-services`: Initialize Kafka topics, MinIO buckets, and database after services are running

**Requirements**:
- OpenSSL
- Bash 4.0+
- Docker (for `--init-services`)

### quick-start.sh

One-command deployment script for local development.

**Usage**:
```bash
./scripts/quick-start.sh
```

**What it does**:
1. Checks prerequisites (Docker, Docker Compose)
2. Runs bootstrap script
3. Starts all services with docker-compose
4. Initializes services
5. Verifies deployment

**Perfect for**: First-time users and local development setup

### demo.sh

Demonstration script showing red→blue→purple security cycle.

**Usage**:
```bash
# Ensure services are running first
docker-compose up -d

# Run demo
./scripts/demo.sh
```

**What it does**:
1. Verifies services are running
2. Simulates a red team attack scenario
3. Shows generated security alerts
4. Demonstrates blue team response
5. Performs purple team gap analysis

**Use cases**:
- Demo for stakeholders
- Testing the complete workflow
- Validating deployment

## Script Details

### Bootstrap Script Architecture

```
bootstrap.sh
├── Phase 1: Local Setup
│   ├── create_directories()
│   ├── generate_secrets()
│   ├── generate_certificates()
│   └── create_env_file()
│
└── Phase 2: Service Initialization (--init-services)
    ├── wait_for_services()
    ├── initialize_kafka()
    ├── initialize_minio()
    └── initialize_database()
```

### Generated Files

After running `bootstrap.sh`:

```
├── secrets/
│   ├── master_key.bin        # AES-256 encryption key
│   ├── jwt_secret.txt         # JWT signing secret
│   ├── db_password.txt        # PostgreSQL password
│   ├── minio_access_key.txt   # MinIO access key
│   ├── minio_secret_key.txt   # MinIO secret key
│   ├── vault_root_token.txt   # Vault root token
│   └── api_key.txt            # API authentication key
│
├── certs/
│   ├── ca-cert.pem            # Certificate Authority
│   ├── ca-key.pem             # CA private key
│   ├── server-cert.pem        # Server certificate
│   └── server-key.pem         # Server private key
│
└── .env                       # Environment configuration
```

### Security Considerations

**Important**: The generated secrets and certificates are suitable for **development only**.

For production:
- Use an external secrets manager (HashiCorp Vault, AWS Secrets Manager)
- Obtain certificates from a trusted Certificate Authority
- Enable TLS/mTLS for all communications
- Implement secret rotation policies

See [SECURITY.md](../SECURITY.md) for detailed security guidelines.

## Customization

### Adding Custom Initialization

To add custom initialization steps, edit `bootstrap.sh`:

```bash
# Add new function
initialize_custom_service() {
    log_info "Initializing custom service..."
    # Your initialization code here
    log_success "Custom service initialized"
}

# Call it in --init-services block
if [ "${1:-}" == "--init-services" ]; then
    wait_for_services
    initialize_kafka
    initialize_minio
    initialize_database
    initialize_custom_service  # Add here
    log_success "All services initialized!"
fi
```

### Modifying Certificate Configuration

Edit the certificate generation section in `bootstrap.sh`:

```bash
# Custom certificate validity
openssl x509 -req -days 3650 ...  # Change from 365 to 3650 days

# Custom Subject Alternative Names (SAN)
cat > "${CERTS_DIR}/server-ext.cnf" << EOF
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = your-domain.com
DNS.3 = *.your-domain.com
IP.1 = 127.0.0.1
IP.2 = your-public-ip
EOF
```

## Troubleshooting

### Bootstrap Fails

```bash
# Check OpenSSL
openssl version

# Check permissions
ls -la scripts/bootstrap.sh
chmod +x scripts/bootstrap.sh

# Run with debug
bash -x scripts/bootstrap.sh
```

### Service Initialization Fails

```bash
# Check Docker is running
docker ps

# Check services are up
docker-compose ps

# View logs
docker-compose logs postgres kafka minio

# Wait longer for services to start
sleep 30
./scripts/bootstrap.sh --init-services
```

### Permission Issues

```bash
# Fix secrets permissions
chmod 700 secrets/
chmod 600 secrets/*

# Fix certificate permissions
chmod 644 certs/*.pem
chmod 600 certs/*-key.pem
```

## Examples

### Complete Fresh Deployment

```bash
# 1. Clone repository
git clone https://github.com/perryjr1444-ux/jigglesmccrusty.git
cd jigglesmccrusty

# 2. Quick start (one command)
./scripts/quick-start.sh

# Or step-by-step:

# 2a. Bootstrap
./scripts/bootstrap.sh

# 2b. Start services
docker-compose up -d

# 2c. Initialize
./scripts/bootstrap.sh --init-services

# 3. Verify
make health

# 4. Run demo
./scripts/demo.sh
```

### Re-initialization

```bash
# Restart services without losing data
docker-compose restart

# Recreate services from scratch
docker-compose down
docker-compose up -d
./scripts/bootstrap.sh --init-services
```

### Complete Reset

```bash
# WARNING: Deletes all data
docker-compose down -v
rm -rf secrets/ certs/ data/ .env
./scripts/bootstrap.sh
docker-compose up -d
./scripts/bootstrap.sh --init-services
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Bootstrap environment
  run: ./scripts/bootstrap.sh

- name: Start services
  run: docker-compose up -d

- name: Initialize services
  run: ./scripts/bootstrap.sh --init-services

- name: Run tests
  run: ./scripts/demo.sh
```

### GitLab CI

```yaml
bootstrap:
  script:
    - ./scripts/bootstrap.sh
    - docker-compose up -d
    - ./scripts/bootstrap.sh --init-services
    - make health
```

## Contributing

When adding new scripts:

1. Make them executable: `chmod +x scripts/new-script.sh`
2. Add shebang: `#!/usr/bin/env bash`
3. Use `set -euo pipefail` for error handling
4. Add usage documentation in comments
5. Update this README

## Related Documentation

- [DEPLOYMENT.md](../DEPLOYMENT.md) - Complete deployment guide
- [SECURITY.md](../SECURITY.md) - Security best practices
- [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) - Troubleshooting guide
- [README.md](../README.md) - Project overview

---

**Last Updated**: Generated with bootstrap deployment implementation
**Version**: 0.1.0
