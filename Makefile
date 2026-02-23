# Antigravity Workspace - Makefile
# Usage: make <command>

.PHONY: help install install-dev test lint format clean run

# Default target
help:
	@echo "Available commands:"
	@echo "  make install      Install production dependencies"
	@echo "  make install-dev  Install development dependencies"
	@echo "  make test         Run tests with coverage"
	@echo "  make lint         Run linting checks"
	@echo "  make format       Format code with ruff"
	@echo "  make clean        Remove cache files"
	@echo "  make run          Start development server"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

# Testing
test:
	pytest --cov=src --cov-report=term-missing --cov-report=html

test-unit:
	pytest tests/unit -v

test-integration:
	pytest tests/integration -v

# Linting
lint:
	ruff check src/ tests/
	mypy src/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

# Cleanup
clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Development server
run:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Health check
health:
	curl -s http://localhost:8000/health | python -m json.tool
