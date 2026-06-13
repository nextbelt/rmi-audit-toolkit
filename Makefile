# RMI Audit Toolkit — dev orchestration (Docker Compose)
#
# Prerequisites: Docker Desktop (or Docker Engine + Compose plugin) running.
# First time only:
#   cp .env.example .env          # then edit .env if you have optional keys
#   make build                    # build both images (~3 min)
#   make up                       # start backend + frontend
#
# Day-to-day:
#   make up       start (or restart) the whole dev stack
#   make stop     stop containers without removing them
#   make logs     tail live logs from both services
#   make test     run pytest inside the backend container
#   make shell-be open a bash shell in the backend container
#   make shell-fe open a sh shell in the frontend container
#   make destroy  stop + wipe containers, networks, named volumes

.PHONY: up stop build rebuild logs test shell-be shell-fe destroy \
        typecheck lint ci-check help

DC := docker compose

# ── Lifecycle ────────────────────────────────────────────────────────────────

up:           ## Start backend + frontend (build images if missing)
	$(DC) up --build -d
	@echo ""
	@echo "  Backend  → http://localhost:8000"
	@echo "  Frontend → http://localhost:3000"
	@echo "  Docs     → http://localhost:8000/docs"
	@echo ""
	@echo "  Logs:  make logs"
	@echo "  Stop:  make stop"

stop:         ## Stop containers (data is preserved)
	$(DC) stop

build:        ## Build both Docker images
	$(DC) build

rebuild:      ## Force-rebuild both images from scratch (no cache)
	$(DC) build --no-cache

destroy:      ## Stop + remove containers, networks, and named volumes
	$(DC) down -v

logs:         ## Tail logs from all services (Ctrl-C to exit)
	$(DC) logs -f

logs-be:      ## Tail backend logs only
	$(DC) logs -f backend

logs-fe:      ## Tail frontend logs only
	$(DC) logs -f frontend

# ── Development shortcuts ────────────────────────────────────────────────────

shell-be:     ## Bash shell inside the running backend container
	$(DC) exec backend bash

shell-fe:     ## Sh shell inside the running frontend container
	$(DC) exec frontend sh

test:         ## Run pytest inside the running backend container
	$(DC) exec backend pytest -q --tb=short

typecheck:    ## TypeScript type-check inside the running frontend container
	$(DC) exec frontend npm run typecheck

lint:         ## ESLint inside the running frontend container
	$(DC) exec frontend npm run lint

# ── Quality gate (mirrors CI) ────────────────────────────────────────────────

ci-check:     ## Run the same checks CI runs (pytest + tsc + build) in containers
	$(DC) exec backend  pytest -q --tb=short
	$(DC) exec frontend npm run typecheck
	$(DC) exec frontend npm run build

help:         ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

