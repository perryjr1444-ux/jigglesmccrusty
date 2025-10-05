.PHONY: help bootstrap start stop restart clean logs status health test

# Default target
.DEFAULT_GOAL := help

# Color output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)AI SOC Multi-Agent Framework$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(BLUE)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

bootstrap: ## Initialize secrets, certificates, and configuration
	@echo "$(BLUE)Running bootstrap script...$(NC)"
	./scripts/bootstrap.sh

start: ## Start all services
	@echo "$(BLUE)Starting all services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started. Initializing...$(NC)"
	@sleep 10
	./scripts/bootstrap.sh --init-services
	@echo "$(GREEN)All services are ready!$(NC)"

stop: ## Stop all services
	@echo "$(BLUE)Stopping all services...$(NC)"
	docker-compose stop

restart: stop start ## Restart all services

down: ## Stop and remove containers, networks
	@echo "$(RED)Stopping and removing containers...$(NC)"
	docker-compose down

clean: ## Remove containers, networks, and volumes (WARNING: DATA LOSS)
	@echo "$(RED)WARNING: This will remove all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		rm -rf secrets/ certs/ data/ .env; \
		echo "$(GREEN)Cleanup complete$(NC)"; \
	fi

logs: ## Show logs from all services
	docker-compose logs -f

logs-ai-soc: ## Show logs from AI SOC service
	docker-compose logs -f ai-soc

logs-frontend: ## Show logs from frontend service
	docker-compose logs -f frontend

status: ## Show status of all services
	@echo "$(BLUE)Service Status:$(NC)"
	@docker-compose ps

health: ## Check health of all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@echo -n "AI SOC:    "
	@curl -sf http://localhost:9000/health > /dev/null && echo "$(GREEN)✓ Healthy$(NC)" || echo "$(RED)✗ Unhealthy$(NC)"
	@echo -n "Frontend:  "
	@curl -sf http://localhost:8000/health > /dev/null && echo "$(GREEN)✓ Healthy$(NC)" || echo "$(RED)✗ Unhealthy$(NC)"
	@echo -n "Postgres:  "
	@docker exec ai-soc-postgres pg_isready -U aisoc > /dev/null 2>&1 && echo "$(GREEN)✓ Healthy$(NC)" || echo "$(RED)✗ Unhealthy$(NC)"
	@echo -n "Redis:     "
	@docker exec ai-soc-redis redis-cli ping > /dev/null 2>&1 && echo "$(GREEN)✓ Healthy$(NC)" || echo "$(RED)✗ Unhealthy$(NC)"
	@echo -n "MinIO:     "
	@curl -sf http://localhost:9000/minio/health/live > /dev/null && echo "$(GREEN)✓ Healthy$(NC)" || echo "$(RED)✗ Unhealthy$(NC)"

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	cd ai_soc && docker-compose exec -T ai-soc pytest

build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose build

pull: ## Pull latest Docker images
	@echo "$(BLUE)Pulling latest Docker images...$(NC)"
	docker-compose pull

ps: status ## Alias for status

shell-ai-soc: ## Open shell in AI SOC container
	docker exec -it ai-soc-service bash

shell-postgres: ## Open PostgreSQL shell
	docker exec -it ai-soc-postgres psql -U aisoc -d aisoc

shell-redis: ## Open Redis CLI
	docker exec -it ai-soc-redis redis-cli

backup: ## Backup PostgreSQL and MinIO data
	@echo "$(BLUE)Creating backups...$(NC)"
	@mkdir -p backups
	@docker run --rm -v ai-soc_postgres_data:/data -v $$(pwd)/backups:/backup \
		alpine tar czf /backup/postgres-$$(date +%Y%m%d-%H%M%S).tar.gz /data
	@docker run --rm -v ai-soc_minio_data:/data -v $$(pwd)/backups:/backup \
		alpine tar czf /backup/minio-$$(date +%Y%m%d-%H%M%S).tar.gz /data
	@echo "$(GREEN)Backups created in ./backups/$(NC)"

dev: ## Start services in development mode with live reload
	@echo "$(BLUE)Starting in development mode...$(NC)"
	docker-compose up

deploy: bootstrap build start health ## Full deployment (bootstrap + build + start + health check)
	@echo "$(GREEN)Deployment complete!$(NC)"
	@echo "Access the application at: http://localhost:8000"
	@echo "AI SOC API available at: http://localhost:9000"
