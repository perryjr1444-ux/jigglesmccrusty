#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Bootstrap Script for AI SOC Multi-Agent Framework
# ============================================================================
# This script initializes the environment by:
# - Generating secrets (master key, JWT secret, API keys)
# - Creating TLS certificates for secure communication
# - Initializing database schemas
# - Setting up Kafka topics
# - Provisioning MinIO buckets
# - Configuring Vault secrets
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SECRETS_DIR="${PROJECT_ROOT}/secrets"
CERTS_DIR="${PROJECT_ROOT}/certs"
DATA_DIR="${PROJECT_ROOT}/data"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ============================================================================
# 1. Create directory structure
# ============================================================================
create_directories() {
    log_info "Creating directory structure..."
    mkdir -p "${SECRETS_DIR}"
    mkdir -p "${CERTS_DIR}"
    mkdir -p "${DATA_DIR}/postgres"
    mkdir -p "${DATA_DIR}/redis"
    mkdir -p "${DATA_DIR}/kafka"
    mkdir -p "${DATA_DIR}/minio"
    mkdir -p "${DATA_DIR}/vault"
    
    # Set secure permissions
    chmod 700 "${SECRETS_DIR}"
    chmod 755 "${CERTS_DIR}"
    
    log_success "Directory structure created"
}

# ============================================================================
# 2. Generate secrets
# ============================================================================
generate_secrets() {
    log_info "Generating secrets..."
    
    # Generate master encryption key (32 bytes for AES-256)
    if [ ! -f "${SECRETS_DIR}/master_key.bin" ]; then
        openssl rand -out "${SECRETS_DIR}/master_key.bin" 32
        chmod 600 "${SECRETS_DIR}/master_key.bin"
        log_success "Generated master encryption key"
    else
        log_warning "Master key already exists, skipping generation"
    fi
    
    # Generate JWT secret
    if [ ! -f "${SECRETS_DIR}/jwt_secret.txt" ]; then
        openssl rand -base64 64 > "${SECRETS_DIR}/jwt_secret.txt"
        chmod 600 "${SECRETS_DIR}/jwt_secret.txt"
        log_success "Generated JWT secret"
    else
        log_warning "JWT secret already exists, skipping generation"
    fi
    
    # Generate database password
    if [ ! -f "${SECRETS_DIR}/db_password.txt" ]; then
        openssl rand -base64 32 > "${SECRETS_DIR}/db_password.txt"
        chmod 600 "${SECRETS_DIR}/db_password.txt"
        log_success "Generated database password"
    else
        log_warning "Database password already exists, skipping generation"
    fi
    
    # Generate MinIO credentials
    if [ ! -f "${SECRETS_DIR}/minio_access_key.txt" ]; then
        openssl rand -base64 20 | tr -d '/+=' | head -c 20 > "${SECRETS_DIR}/minio_access_key.txt"
        chmod 600 "${SECRETS_DIR}/minio_access_key.txt"
        log_success "Generated MinIO access key"
    else
        log_warning "MinIO access key already exists, skipping generation"
    fi
    
    if [ ! -f "${SECRETS_DIR}/minio_secret_key.txt" ]; then
        openssl rand -base64 40 > "${SECRETS_DIR}/minio_secret_key.txt"
        chmod 600 "${SECRETS_DIR}/minio_secret_key.txt"
        log_success "Generated MinIO secret key"
    else
        log_warning "MinIO secret key already exists, skipping generation"
    fi
    
    # Generate Vault root token
    if [ ! -f "${SECRETS_DIR}/vault_root_token.txt" ]; then
        openssl rand -base64 32 > "${SECRETS_DIR}/vault_root_token.txt"
        chmod 600 "${SECRETS_DIR}/vault_root_token.txt"
        log_success "Generated Vault root token"
    else
        log_warning "Vault root token already exists, skipping generation"
    fi
    
    # Generate API key for external services
    if [ ! -f "${SECRETS_DIR}/api_key.txt" ]; then
        openssl rand -hex 32 > "${SECRETS_DIR}/api_key.txt"
        chmod 600 "${SECRETS_DIR}/api_key.txt"
        log_success "Generated API key"
    else
        log_warning "API key already exists, skipping generation"
    fi
}

# ============================================================================
# 3. Generate TLS certificates
# ============================================================================
generate_certificates() {
    log_info "Generating TLS certificates..."
    
    # Generate CA private key and certificate
    if [ ! -f "${CERTS_DIR}/ca-key.pem" ]; then
        openssl genrsa -out "${CERTS_DIR}/ca-key.pem" 4096
        openssl req -new -x509 -days 3650 -key "${CERTS_DIR}/ca-key.pem" \
            -out "${CERTS_DIR}/ca-cert.pem" \
            -subj "/C=US/ST=State/L=City/O=AI-SOC/OU=Security/CN=AI-SOC-CA"
        log_success "Generated CA certificate"
    else
        log_warning "CA certificate already exists, skipping generation"
    fi
    
    # Generate server certificate for services
    if [ ! -f "${CERTS_DIR}/server-key.pem" ]; then
        openssl genrsa -out "${CERTS_DIR}/server-key.pem" 2048
        openssl req -new -key "${CERTS_DIR}/server-key.pem" \
            -out "${CERTS_DIR}/server.csr" \
            -subj "/C=US/ST=State/L=City/O=AI-SOC/OU=Services/CN=localhost"
        
        # Create extensions file for SAN
        cat > "${CERTS_DIR}/server-ext.cnf" << EOF
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = ai-soc
DNS.3 = api
DNS.4 = postgres
DNS.5 = redis
DNS.6 = kafka
DNS.7 = minio
DNS.8 = vault
IP.1 = 127.0.0.1
IP.2 = ::1
EOF
        
        openssl x509 -req -days 365 -in "${CERTS_DIR}/server.csr" \
            -CA "${CERTS_DIR}/ca-cert.pem" -CAkey "${CERTS_DIR}/ca-key.pem" \
            -CAcreateserial -out "${CERTS_DIR}/server-cert.pem" \
            -extfile "${CERTS_DIR}/server-ext.cnf"
        
        rm "${CERTS_DIR}/server.csr" "${CERTS_DIR}/server-ext.cnf"
        log_success "Generated server certificate"
    else
        log_warning "Server certificate already exists, skipping generation"
    fi
    
    # Set appropriate permissions
    chmod 644 "${CERTS_DIR}"/*.pem
    chmod 600 "${CERTS_DIR}"/*-key.pem
}

# ============================================================================
# 4. Create environment file
# ============================================================================
create_env_file() {
    log_info "Creating .env file from template..."
    
    if [ ! -f "${PROJECT_ROOT}/.env" ]; then
        # Read secrets
        DB_PASSWORD=$(cat "${SECRETS_DIR}/db_password.txt")
        JWT_SECRET=$(cat "${SECRETS_DIR}/jwt_secret.txt")
        MINIO_ACCESS_KEY=$(cat "${SECRETS_DIR}/minio_access_key.txt")
        MINIO_SECRET_KEY=$(cat "${SECRETS_DIR}/minio_secret_key.txt")
        VAULT_TOKEN=$(cat "${SECRETS_DIR}/vault_root_token.txt")
        API_KEY=$(cat "${SECRETS_DIR}/api_key.txt")
        
        cat > "${PROJECT_ROOT}/.env" << EOF
# ============================================================================
# AI SOC Environment Configuration
# Generated by bootstrap.sh on $(date)
# ============================================================================

# Database Configuration
POSTGRES_USER=aisoc
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=aisoc
DATABASE_URL=postgresql://aisoc:${DB_PASSWORD}@postgres:5432/aisoc

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_GROUP_ID=ai-soc

# MinIO Configuration
MINIO_ROOT_USER=${MINIO_ACCESS_KEY}
MINIO_ROOT_PASSWORD=${MINIO_SECRET_KEY}
MINIO_ENDPOINT=minio:9000
MINIO_BUCKET=ai-soc-artifacts

# Vault Configuration
VAULT_ADDR=http://vault:8200
VAULT_TOKEN=${VAULT_TOKEN}

# AI SOC Service Configuration
AI_SOC_SERVICE_NAME=ai-soc
AI_SOC_KAFKA_BOOTSTRAP_SERVERS=kafka:9092
AI_SOC_KAFKA_GROUP_ID=ai-soc
AI_SOC_ALERTS_TOPIC=rbp.alerts
AI_SOC_QUOTA_UPDATES_TOPIC=rbp.quota_updates

# API Configuration
API_PORT=8000
API_KEY=${API_KEY}
JWT_SECRET=${JWT_SECRET}

# Security
MASTER_KEY_PATH=/run/secrets/master_key.bin

# Logging
LOG_LEVEL=INFO
EOF
        chmod 600 "${PROJECT_ROOT}/.env"
        log_success "Created .env file"
    else
        log_warning ".env file already exists, skipping creation"
    fi
}

# ============================================================================
# 5. Wait for services and initialize
# ============================================================================
wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # This function is called after docker-compose up
    # Check if we're in a docker environment
    if command -v docker &> /dev/null && docker ps &> /dev/null; then
        log_info "Checking Docker services..."
        
        # Wait for PostgreSQL
        log_info "Waiting for PostgreSQL..."
        for i in {1..30}; do
            if docker exec ai-soc-postgres pg_isready -U aisoc &> /dev/null; then
                log_success "PostgreSQL is ready"
                break
            fi
            sleep 2
        done
        
        # Wait for Redis
        log_info "Waiting for Redis..."
        for i in {1..30}; do
            if docker exec ai-soc-redis redis-cli ping &> /dev/null; then
                log_success "Redis is ready"
                break
            fi
            sleep 2
        done
        
        # Wait for Kafka
        log_info "Waiting for Kafka..."
        sleep 10
        log_success "Kafka should be ready"
        
        # Wait for MinIO
        log_info "Waiting for MinIO..."
        for i in {1..30}; do
            if docker exec ai-soc-minio mc ready local &> /dev/null; then
                log_success "MinIO is ready"
                break
            fi
            sleep 2
        done
    else
        log_warning "Docker not available, skipping service checks"
    fi
}

# ============================================================================
# 6. Initialize Kafka topics
# ============================================================================
initialize_kafka() {
    log_info "Initializing Kafka topics..."
    
    if command -v docker &> /dev/null && docker ps | grep -q kafka; then
        TOPICS=(
            "rbp.metrics"
            "rbp.proposals"
            "rbp.approvals"
            "rbp.alerts"
            "rbp.quota_updates"
            "red-scenarios"
            "blue-responses"
            "purple-gaps"
        )
        
        for topic in "${TOPICS[@]}"; do
            docker exec ai-soc-kafka kafka-topics.sh \
                --bootstrap-server localhost:9092 \
                --create --if-not-exists \
                --topic "${topic}" \
                --partitions 3 \
                --replication-factor 1 \
                2>/dev/null && log_success "Created topic: ${topic}" || log_warning "Topic ${topic} may already exist"
        done
    else
        log_warning "Kafka not available, skipping topic creation"
    fi
}

# ============================================================================
# 7. Initialize MinIO buckets
# ============================================================================
initialize_minio() {
    log_info "Initializing MinIO buckets..."
    
    if command -v docker &> /dev/null && docker ps | grep -q minio; then
        MINIO_ACCESS_KEY=$(cat "${SECRETS_DIR}/minio_access_key.txt")
        MINIO_SECRET_KEY=$(cat "${SECRETS_DIR}/minio_secret_key.txt")
        
        docker exec ai-soc-minio mc alias set local http://localhost:9000 "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}" 2>/dev/null || true
        docker exec ai-soc-minio mc mb local/ai-soc-artifacts --ignore-existing 2>/dev/null && log_success "Created MinIO bucket: ai-soc-artifacts" || log_warning "MinIO bucket may already exist"
        docker exec ai-soc-minio mc mb local/ai-soc-models --ignore-existing 2>/dev/null && log_success "Created MinIO bucket: ai-soc-models" || log_warning "MinIO bucket may already exist"
    else
        log_warning "MinIO not available, skipping bucket creation"
    fi
}

# ============================================================================
# 8. Initialize database schema
# ============================================================================
initialize_database() {
    log_info "Initializing database schema..."
    
    if command -v docker &> /dev/null && docker ps | grep -q postgres; then
        cat > /tmp/init_schema.sql << 'EOF'
-- AI SOC Database Schema
CREATE TABLE IF NOT EXISTS alerts (
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

CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at DESC);

CREATE TABLE IF NOT EXISTS telemetry_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(64) UNIQUE NOT NULL,
    source VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_telemetry_source ON telemetry_events(source);
CREATE INDEX IF NOT EXISTS idx_telemetry_type ON telemetry_events(event_type);
CREATE INDEX IF NOT EXISTS idx_telemetry_created ON telemetry_events(created_at DESC);

CREATE TABLE IF NOT EXISTS quota_updates (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    reason TEXT,
    self_suggest_enabled BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quota_agent ON quota_updates(agent_id);
CREATE INDEX IF NOT EXISTS idx_quota_created ON quota_updates(created_at DESC);
EOF
        
        docker exec -i ai-soc-postgres psql -U aisoc -d aisoc < /tmp/init_schema.sql
        rm /tmp/init_schema.sql
        log_success "Database schema initialized"
    else
        log_warning "PostgreSQL not available, skipping schema initialization"
    fi
}

# ============================================================================
# Main execution
# ============================================================================
main() {
    echo ""
    echo "============================================================================"
    echo "AI SOC Multi-Agent Framework Bootstrap"
    echo "============================================================================"
    echo ""
    
    create_directories
    generate_secrets
    generate_certificates
    create_env_file
    
    echo ""
    log_success "Bootstrap phase 1 complete!"
    echo ""
    log_info "Next steps:"
    echo "  1. Review the generated .env file and adjust if needed"
    echo "  2. Start services with: docker-compose up -d"
    echo "  3. Run initialization with: ./scripts/bootstrap.sh --init-services"
    echo ""
}

# Check for service initialization flag
if [ "${1:-}" == "--init-services" ]; then
    wait_for_services
    initialize_kafka
    initialize_minio
    initialize_database
    log_success "All services initialized!"
else
    main
fi
