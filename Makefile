.PHONY: help up down restart ps logs backend-test frontend-test test lint

help:
	@echo "EV Fleet Data Platform"
	@echo ""
	@echo "Available targets:"
	@echo "  make up             Start the local platform"
	@echo "  make down           Stop the local platform"
	@echo "  make restart        Restart the local platform"
	@echo "  make ps             Show running containers"
	@echo "  make logs           Show Compose logs"
	@echo "  make backend-test   Run backend tests"
	@echo "  make frontend-test  Run frontend tests/build"
	@echo "  make test           Run the primary local test targets"
	@echo "  make lint           Run lightweight repository checks"

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose down
	docker compose up -d

ps:
	docker compose ps

logs:
	docker compose logs --tail=200

backend-test:
	docker compose run --rm backend pytest

frontend-test:
	docker compose run --rm frontend npm run build

test: backend-test frontend-test

lint:
	docker compose config
	python -m compileall backend
