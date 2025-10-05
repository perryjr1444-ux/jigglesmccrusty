#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Quick Start Script for AI SOC Multi-Agent Framework
# ============================================================================
# This script provides a one-command deployment for local development
# ============================================================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  AI SOC Multi-Agent Framework - Quick Start"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Check prerequisites
check_prerequisites() {
    echo -e "${BLUE}[1/5]${NC} Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}Docker not found. Please install Docker first.${NC}"
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${YELLOW}Docker Compose not found. Please install Docker Compose first.${NC}"
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"
}

# Bootstrap
run_bootstrap() {
    echo ""
    echo -e "${BLUE}[2/5]${NC} Generating secrets and certificates..."
    cd "${PROJECT_ROOT}"
    ./scripts/bootstrap.sh
    echo -e "${GREEN}✓ Bootstrap complete${NC}"
}

# Start services
start_services() {
    echo ""
    echo -e "${BLUE}[3/5]${NC} Starting all services..."
    cd "${PROJECT_ROOT}"
    docker-compose up -d
    echo -e "${GREEN}✓ Services started${NC}"
}

# Initialize
initialize_services() {
    echo ""
    echo -e "${BLUE}[4/5]${NC} Waiting for services to be ready..."
    sleep 15
    
    echo "Initializing Kafka topics, MinIO buckets, and database..."
    cd "${PROJECT_ROOT}"
    ./scripts/bootstrap.sh --init-services
    echo -e "${GREEN}✓ Services initialized${NC}"
}

# Verify
verify_deployment() {
    echo ""
    echo -e "${BLUE}[5/5]${NC} Verifying deployment..."
    
    # Wait a bit more for services to stabilize
    sleep 5
    
    # Check AI SOC
    if curl -sf http://localhost:9000/health > /dev/null; then
        echo -e "${GREEN}✓ AI SOC service is healthy${NC}"
    else
        echo -e "${YELLOW}⚠ AI SOC service is not responding yet${NC}"
    fi
    
    # Check Frontend
    if curl -sf http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✓ Frontend is healthy${NC}"
    else
        echo -e "${YELLOW}⚠ Frontend is not responding yet${NC}"
    fi
}

# Display success message
show_success() {
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "Access the application:"
    echo -e "  ${BLUE}Frontend:${NC}     http://localhost:8000"
    echo -e "  ${BLUE}AI SOC API:${NC}   http://localhost:9000"
    echo -e "  ${BLUE}MinIO Console:${NC} http://localhost:9001"
    echo -e "  ${BLUE}Vault UI:${NC}     http://localhost:8200"
    echo ""
    echo "Useful commands:"
    echo "  make status    - Check service status"
    echo "  make logs      - View service logs"
    echo "  make health    - Check service health"
    echo "  make stop      - Stop all services"
    echo "  make help      - Show all available commands"
    echo ""
    echo "View logs: docker-compose logs -f"
    echo ""
}

# Main execution
main() {
    cd "${PROJECT_ROOT}"
    
    check_prerequisites
    run_bootstrap
    start_services
    initialize_services
    verify_deployment
    show_success
}

main
