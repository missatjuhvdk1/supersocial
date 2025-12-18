# TikTok Auto-Poster - Docker Management Makefile

.PHONY: help build up down restart logs ps clean build-backend build-frontend build-worker migrate shell-backend shell-frontend shell-db test

# Default target
help:
	@echo "TikTok Auto-Poster - Docker Commands"
	@echo "===================================="
	@echo "build              - Build all Docker images"
	@echo "build-backend      - Build backend image only"
	@echo "build-frontend     - Build frontend image only"
	@echo "up                 - Start all services"
	@echo "down               - Stop all services"
	@echo "restart            - Restart all services"
	@echo "logs               - View logs from all services"
	@echo "logs-backend       - View backend logs"
	@echo "logs-frontend      - View frontend logs"
	@echo "logs-worker        - View worker logs"
	@echo "ps                 - List running containers"
	@echo "clean              - Stop and remove containers, volumes"
	@echo "migrate            - Run database migrations"
	@echo "shell-backend      - Open shell in backend container"
	@echo "shell-frontend     - Open shell in frontend container"
	@echo "shell-db           - Open psql in database"
	@echo "shell-redis        - Open redis-cli"
	@echo "test               - Run backend tests"
	@echo "dev                - Start in development mode"
	@echo "prod               - Start in production mode"

# Build all images
build:
	docker-compose build

# Build specific services
build-backend:
	docker-compose build backend worker beat

build-frontend:
	docker-compose build frontend

# Start services
up:
	docker-compose up -d

# Start with logs
up-logs:
	docker-compose up

# Development mode
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production mode
prod:
	docker-compose up -d

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-worker:
	docker-compose logs -f worker

logs-beat:
	docker-compose logs -f beat

# List containers
ps:
	docker-compose ps

# Clean up everything
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Deep clean (including images)
clean-all:
	docker-compose down -v --rmi all --remove-orphans
	docker system prune -af

# Database migrations
migrate:
	docker-compose exec backend alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	docker-compose exec backend alembic revision --autogenerate -m "$$msg"

migrate-downgrade:
	docker-compose exec backend alembic downgrade -1

# Shell access
shell-backend:
	docker-compose exec backend /bin/bash

shell-frontend:
	docker-compose exec frontend /bin/sh

shell-db:
	docker-compose exec postgres psql -U tiktok -d tiktok_db

shell-redis:
	docker-compose exec redis redis-cli -a redis_password

# Testing
test:
	docker-compose exec backend pytest

test-cov:
	docker-compose exec backend pytest --cov=app --cov-report=html

# Health checks
health:
	@echo "Backend Health:"
	@curl -f http://localhost:8000/health || echo "Backend not healthy"
	@echo "\nFrontend Health:"
	@curl -f http://localhost:3000/api/health || echo "Frontend not healthy"

# Monitor Celery workers
celery-status:
	docker-compose exec worker celery -A app.celery inspect active

celery-stats:
	docker-compose exec worker celery -A app.celery inspect stats

# Database backup
db-backup:
	docker-compose exec postgres pg_dump -U tiktok tiktok_db > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Database restore
db-restore:
	@read -p "Enter backup file path: " file; \
	docker-compose exec -T postgres psql -U tiktok -d tiktok_db < $$file

# View environment variables
env:
	docker-compose config

# Pull latest images
pull:
	docker-compose pull

# Rebuild and restart specific service
rebuild-backend:
	docker-compose up -d --no-deps --build backend worker beat

rebuild-frontend:
	docker-compose up -d --no-deps --build frontend
