.DEFAULT_GOAL := help

# Параметры замера: make run URL=<адрес> REQUESTS=5 TIMEOUT=60
URL ?= https://proof.ovh.net/files/10Mb.dat
REQUESTS ?= 10
TIMEOUT ?= 30

.PHONY: help sync run format lint format-check typecheck test check build clean

help: ## Показать список команд
	@echo "Доступные команды:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

sync: ## Создать .venv и установить зависимости (uv sync)
	uv sync

run: ## Замерить адрес: make run URL=<адрес> [REQUESTS=10] [TIMEOUT=30]
	uv run http-speed-meter -n "$(REQUESTS)" -t "$(TIMEOUT)" "$(URL)"

format: ## Отформатировать код (ruff format)
	uv run ruff format .

lint: ## Проверить код линтером (ruff check)
	uv run ruff check .

format-check: ## Проверить форматирование без правок (ruff format --check)
	uv run ruff format --check .

typecheck: ## Проверить типы (mypy, strict)
	uv run mypy

test: ## Прогнать тесты (pytest)
	uv run pytest

check: format-check lint typecheck test

build: ## Собрать пакет в dist/ (uv build)
	uv build

clean: ## Удалить кэши, dist/ и .venv
	rm -rf .venv .pytest_cache .mypy_cache .ruff_cache dist build
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +