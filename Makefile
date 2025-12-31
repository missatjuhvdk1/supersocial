# ===========================================
# Industry-Standard Makefile for Docker
# TikTok Auto-Poster Application
# ===========================================

.PHONY: help build up down restart logs shell test clean prune

# Default target
.DEFAULT_GOAL := help

# Colors for terminal output
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m

# ===========================================
# Help
# ===========================================
help: ## Show this help message
	@echo ""
	@echo "$(BLUE)TikTok Auto-Poster - Docker Commands$(NC)"
	@echo "======================================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ===========================================
# Build Commands
# ===========================================
build: ## Build all Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker compose build

build-no-cache: ## Build all Docker images without cache
	@echo "$(BLUE)Building Docker images (no cache)...$(NC)"
	docker compose build --no-cache

build-frontend: ## Build only frontend image
	@echo "$(BLUE)Building frontend image...$(NC)"
	docker compose build frontend

build-backend: ## Build only backend image
	@echo "$(BLUE)Building backend image...$(NC)"
	docker compose build backend

# ===========================================
# Run Commands
# ===========================================
up: ## Start all services in production mode
	@echo "$(GREEN)Starting production services...$(NC)"
	docker compose up -d

up-build: ## Build and start all services
	@echo "$(GREEN)Building and starting services...$(NC)"
	docker compose up -d --build

dev: ## Start all services in development mode
	@echo "$(YELLOW)Starting development services...$(NC)"
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

dev-build: ## Build and start all services in development mode
	@echo "$(YELLOW)Building and starting development services...$(NC)"
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

down: ## Stop all services
	@echo "$(RED)Stopping services...$(NC)"
	docker compose down

down-v: ## Stop all services and remove volumes
	@echo "$(RED)Stopping services and removing volumes...$(NC)"
	docker compose down -v

restart: down up ## Restart all services

# ===========================================
# Logs Commands
# ===========================================
logs: ## View logs from all services
	docker compose logs -f

logs-backend: ## View backend logs
	docker compose logs -f backend

logs-worker: ## View worker logs
	docker compose logs -f worker

logs-frontend: ## View frontend logs
	docker compose logs -f frontend

logs-postgres: ## View PostgreSQL logs
	docker compose logs -f postgres

logs-redis: ## View Redis logs
	docker compose logs -f redis

# ===========================================
# Shell Access
# ===========================================
shell-backend: ## Open shell in backend container
	docker compose exec backend /bin/bash

shell-worker: ## Open shell in worker container
	docker compose exec worker /bin/bash

shell-frontend: ## Open shell in frontend container
	docker compose exec frontend /bin/sh

shell-db: ## Open PostgreSQL shell
	docker compose exec postgres psql -U $${POSTGRES_USER:-tiktok} -d $${POSTGRES_DB:-tiktok_db}

shell-redis: ## Open Redis CLI
	docker compose exec redis redis-cli -a $${REDIS_PASSWORD:-redis_password}

# ===========================================
# Database Commands
# ===========================================
migrate: ## Run database migrations
	@echo "$(BLUE)Running migrations...$(NC)"
	docker compose exec backend alembic upgrade head

migrate-down: ## Rollback last migration
	@echo "$(YELLOW)Rolling back migration...$(NC)"
	docker compose exec backend alembic downgrade -1

migrate-create: ## Create new migration (usage: make migrate-create MSG="description")
	@echo "$(BLUE)Creating migration...$(NC)"
	docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

db-backup: ## Backup database
	@echo "$(BLUE)Backing up database...$(NC)"
	docker compose exec postgres pg_dump -U $${POSTGRES_USER:-tiktok} $${POSTGRES_DB:-tiktok_db} > backup_$$(date +%Y%m%d_%H%M%S).sql

db-restore: ## Restore database (usage: make db-restore FILE=backup.sql)
	@echo "$(YELLOW)Restoring database from $(FILE)...$(NC)"
	docker compose exec -T postgres psql -U $${POSTGRES_USER:-tiktok} -d $${POSTGRES_DB:-tiktok_db} < $(FILE)

# ===========================================
# Testing Commands
# ===========================================
test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	docker compose exec backend pytest

test-cov: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	docker compose exec backend pytest --cov=app --cov-report=html

lint: ## Run linters
	@echo "$(BLUE)Running linters...$(NC)"
	docker compose exec backend flake8 app
	docker compose exec frontend bun run lint

# ===========================================
# Health & Status Commands
# ===========================================
health: ## Check health of all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

ps: ## Show running containers
	docker compose ps

status: ## Show detailed status of all containers
	docker compose ps -a

stats: ## Show resource usage of all containers
	docker stats --no-stream

# ===========================================
# Celery Commands
# ===========================================
celery-status: ## Check Celery worker status
	docker compose exec worker celery -A app.worker.celery_app inspect active

celery-stats: ## Check Celery worker statistics
	docker compose exec worker celery -A app.worker.celery_app inspect stats

celery-purge: ## Purge all Celery tasks
	@echo "$(RED)Purging all Celery tasks...$(NC)"
	docker compose exec worker celery -A app.worker.celery_app purge -f

# ===========================================
# Cleanup Commands
# ===========================================
clean: ## Remove stopped containers and unused images
	@echo "$(YELLOW)Cleaning up...$(NC)"
	docker compose down --remove-orphans
	docker image prune -f

clean-all: ## Remove all containers, volumes, and images
	@echo "$(RED)Cleaning everything...$(NC)"
	docker compose down -v --rmi all --remove-orphans

prune: ## Remove all unused Docker resources (DANGEROUS)
	@echo "$(RED)WARNING: This will remove all unused Docker resources!$(NC)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ]
	docker system prune -af --volumes

# ===========================================
# Setup Commands
# ===========================================
setup: ## Initial setup - copy env files and generate secrets
	@echo "$(BLUE)Setting up environment...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)Created .env from .env.example$(NC)"; \
		echo "$(YELLOW)Please update .env with your settings$(NC)"; \
	else \
		echo "$(YELLOW).env already exists$(NC)"; \
	fi
	@echo "$(GREEN)Generating SECRET_KEY...$(NC)"
	@NEW_SECRET=$$(openssl rand -hex 32) && \
	if grep -q "SECRET_KEY=$$" .env 2>/dev/null || grep -q "SECRET_KEY=your_secret" .env 2>/dev/null; then \
		sed -i "s/SECRET_KEY=.*/SECRET_KEY=$$NEW_SECRET/" .env; \
		echo "$(GREEN)SECRET_KEY generated and updated$(NC)"; \
	fi

init: setup build up migrate ## Full initialization: setup, build, start, and migrate
	@echo "$(GREEN)Initialization complete!$(NC)"
	@echo "$(BLUE)Frontend: http://localhost:3000$(NC)"
	@echo "$(BLUE)Backend API: http://localhost:8000$(NC)"
	@echo "$(BLUE)API Docs: http://localhost:8000/docs$(NC)"

# ===========================================
# Production Commands
# ===========================================
prod-deploy: ## Deploy to production
	@echo "$(GREEN)Deploying to production...$(NC)"
	docker compose pull
	docker compose up -d --build
	docker compose exec backend alembic upgrade head
	@echo "$(GREEN)Deployment complete!$(NC)"

prod-rollback: ## Rollback to previous deployment
	@echo "$(YELLOW)Rolling back...$(NC)"
	docker compose exec backend alembic downgrade -1
	docker compose down
	docker compose up -d

# ===========================================
# Pull & Update Commands
# ===========================================
pull: ## Pull latest images
	docker compose pull

rebuild-backend: ## Rebuild and restart backend services
	docker compose up -d --no-deps --build backend worker beat

rebuild-frontend: ## Rebuild and restart frontend
	docker compose up -d --no-deps --build frontend

# ===========================================
# Environment Info
# ===========================================
env: ## Show resolved docker-compose config
	docker compose config
