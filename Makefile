.PHONY: help install install-dev clean test test-cov lint format check run build docs

# Variables
PYTHON := python3
PIP := pip
PROJECT_NAME := python_pubsub_devtools
VENV := .venv

# Default target
help:
	@echo "Available commands:"
	@echo "  make install        - Install the project in production mode"
	@echo "  make install-dev    - Install the project with dev dependencies (editable mode)"
	@echo "  make clean          - Remove build artifacts and cache files"
	@echo "  make test           - Run tests with pytest"
	@echo "  make test-cov       - Run tests with coverage report"
	@echo "  make lint           - Run linting (flake8 and mypy)"
	@echo "  make format         - Format code with black"
	@echo "  make format-check   - Check code formatting without modifying files"
	@echo "  make check          - Run all checks (format-check, lint, test)"
	@echo "  make run            - Run the CLI tool"
	@echo "  make build          - Build distribution packages"
	@echo "  make venv           - Create a virtual environment"
	@echo "  make setup-dev      - Complete dev setup (venv + install-dev)"

# Create virtual environment
venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "Virtual environment created. Activate it with: source $(VENV)/bin/activate"

# Complete development setup
setup-dev: venv
	@echo "Setting up development environment..."
	@. $(VENV)/bin/activate && $(PIP) install --upgrade pip setuptools wheel
	@. $(VENV)/bin/activate && $(PIP) install -e ".[dev]"
	@echo "Development environment ready! Activate it with: source $(VENV)/bin/activate"

# Install in production mode
install:
	$(PIP) install .

# Install in development mode with dev dependencies
install-dev:
	$(PIP) install -e ".[dev]"

# Clean build artifacts and cache
clean:
	@echo "Cleaning up..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "Clean complete!"

# Run tests
test:
	pytest tests/ -v

# Run tests with coverage
test-cov:
	pytest tests/ --cov=$(PROJECT_NAME) --cov-report=html --cov-report=term-missing -v
	@echo "Coverage report generated in htmlcov/index.html"

# Run linting
lint:
	@echo "Running flake8..."
	flake8 $(PROJECT_NAME) tests/ --max-line-length=100 --exclude=__pycache__,.venv,build,dist
	@echo "Running mypy..."
	mypy $(PROJECT_NAME) --ignore-missing-imports

# Format code
format:
	@echo "Formatting code with black..."
	black $(PROJECT_NAME) tests/

# Check code formatting
format-check:
	@echo "Checking code formatting..."
	black $(PROJECT_NAME) tests/ --check

# Run all checks
check: format-check lint test
	@echo "All checks passed!"

# Run the CLI tool
run:
	pubsub-tools --help

# Build distribution packages
build: clean
	@echo "Building distribution packages..."
	$(PYTHON) -m pip install --upgrade build
	$(PYTHON) -m build
	@echo "Build complete! Packages available in dist/"

# Install pre-commit hooks (if using pre-commit)
install-hooks:
	@if command -v pre-commit >/dev/null 2>&1; then \
		pre-commit install; \
		echo "Pre-commit hooks installed"; \
	else \
		echo "pre-commit not installed. Install with: pip install pre-commit"; \
	fi
