.PHONY: help dev dev-api dev-web install build clean docker-up docker-down

help: ## Show this help message
	@echo "TinyWorld Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	@echo "Installing backend dependencies..."
	cd api && uv sync
	@echo "Installing frontend dependencies..."
	cd web && yarn install

dev-api: ## Run backend dev server
	cd api && uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-web: ## Run frontend dev server
	cd web && yarn dev

dev: ## Run both backend and frontend (requires 2 terminals or use make -j2)
	@echo "Starting TinyWorld..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@make -j2 dev-api dev-web

build: ## Build for production
	@echo "Building frontend..."
	cd web && yarn build
	@echo "Frontend built to web/dist"

clean: ## Clean build artifacts and dependencies
	@echo "Cleaning..."
	rm -rf api/.venv api/__pycache__ api/src/__pycache__
	rm -rf web/node_modules web/dist web/yarn.lock
	@echo "Clean complete"

docker-up: ## Start services with Docker Compose
	docker-compose up -d

docker-down: ## Stop Docker services
	docker-compose down

docker-build: ## Build Docker images
	docker-compose build

test-api: ## Run backend tests
	cd api && uv run pytest

lint-api: ## Lint backend code
	cd api && uv run ruff check .

format-api: ## Format backend code
	cd api && uv run ruff format .