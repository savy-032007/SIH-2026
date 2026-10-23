# APAAR platform task runner.
#
# On Windows without GNU make, use the shim with identical target names:
#   ./make.ps1 up        ./make.ps1 seed       ./make.ps1 test
#
# Docker Desktop must be running before `make up`.

COMPOSE := docker compose
API     := $(COMPOSE) exec -T api

.DEFAULT_GOAL := help
.PHONY: help env up down restart logs ps seed generate migrate revision test test-api test-web fmt lint shell psql clean demo-reset

help: ## Show available targets
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

env: ## Create .env from .env.example if missing
	@test -f .env || (cp .env.example .env && echo "created .env from .env.example")

up: env ## Build and start all services (postgres, mock-abc, api, web)
	$(COMPOSE) up -d --build
	@echo ""
	@echo "api    -> http://localhost:$${API_PORT:-8000}/docs"
	@echo "mock   -> http://localhost:$${MOCK_ABC_PORT:-9001}/docs"
	@echo "web    -> http://localhost:$${WEB_PORT:-3000}"
	@echo ""
	@echo "next:  make seed"

down: ## Stop all services (keeps the database volume)
	$(COMPOSE) down

restart: ## Restart the api service
	$(COMPOSE) restart api

logs: ## Tail logs for all services
	$(COMPOSE) logs -f --tail=100

ps: ## Show service status
	$(COMPOSE) ps

generate: ## Regenerate the synthetic dataset only (no DB writes)
	$(API) python -m generator.generate

seed: ## Migrate, generate synthetic data, load it, print demo credentials
	$(API) python -m app.seed.run --reset

migrate: ## Apply database migrations
	$(API) alembic upgrade head

revision: ## Autogenerate a migration: make revision m="add x"
	$(API) alembic revision --autogenerate -m "$(m)"

test: test-api test-web ## Run all tests

test-api: ## Run backend tests
	$(API) pytest -q

test-web: ## Typecheck the web app
	$(COMPOSE) exec -T web npx tsc --noEmit

fmt: ## Format Python sources
	$(API) ruff format app tests ../../data/generator

lint: ## Lint Python sources
	$(API) ruff check app tests

shell: ## Open a shell in the api container
	$(COMPOSE) exec api bash

psql: ## Open a psql prompt
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-apaar} -d $${POSTGRES_DB:-apaar}

clean: ## Stop services and DELETE the database volume and generated data
	$(COMPOSE) down -v
	rm -rf data/seed

demo-reset: ## Full reset for a demo run (implemented in Phase 5)
	@echo "demo-reset lands in Phase 5 (SPEC 12). For now: make clean && make up && make seed"
