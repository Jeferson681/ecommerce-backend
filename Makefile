.PHONY: help install lint format test test-unit test-integration run docker-up docker-down docker-build

help:
	@echo "Available commands:"
	@echo "  make install          Install backend dependencies"
	@echo "  make lint             Run ruff linter and pre-commit"
	@echo "  make format           Format code with ruff-format"
	@echo "  make test             Run full test suite with coverage"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make run              Start uvicorn dev server"
	@echo "  make docker-up        Start all services with docker compose"
	@echo "  make docker-down      Stop all services"
	@echo "  make docker-build     Rebuild docker images"

install:
	pip install -r requirements.txt -r requirements-dev.txt

lint:
	pre-commit run --all-files

format:
	ruff format .

test:
	pytest --cov=backend.app

test-unit:
	pytest -m "not integration"

test-integration:
	pytest -m integration

run:
	uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-build:
	docker compose build
