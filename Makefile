.PHONY: help install lint lint-check format test coverage run dev clean build up down logs restart

.DEFAULT_GOAL := help

help:
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:
	uv sync

lint:
	uv run ruff check github_repo_search_api/ tests/ --fix
	uv run ruff format github_repo_search_api/ tests/
	uv run pyrefly check github_repo_search_api/

lint-check:
	uv run ruff check github_repo_search_api/ tests/
	uv run ruff format github_repo_search_api/ tests/ --check

format:
	uv run ruff format github_repo_search_api/ tests/

test:
	uv run pytest tests/ -v

coverage:
	uv run pytest tests/ -v --cov=github_repo_search_api --cov-report=term-missing --cov-report=html

run:
	uv run python -m github_repo_search_api

dev:
	uv run uvicorn github_repo_search_api.web.application:get_app --reload --factory

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

restart:
	docker compose restart

clean:
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf **/__pycache__/
	rm -rf github_repo_search_api/static/*.csv
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true


