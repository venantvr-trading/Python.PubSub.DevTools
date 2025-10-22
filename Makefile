.PHONY: build-dist \
        clean-artifacts clean-venv \
        help \
        install-dev install-prod \
        quality-check quality-format quality-format-check quality-lint \
        serve-all 5555-serve-event-flow 5556-serve-event-recorder 5557-serve-mock-exchange 5558-serve-scenario-testing \
        setup-dev setup-venv \
        test-coverage test-unit

# ============================================================================
# VARIABLES
# ============================================================================

PYTHON := python3
PIP := pip
PROJECT_NAME := python_pubsub_devtools
PROJECT_PATH := src/python_pubsub_devtools
VENV := .venv
CONFIG := devtools_config.yaml

# ============================================================================
# HELP
# ============================================================================

help:
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║          PubSub DevTools - Makefile Commands                     ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📦 Build:"
	@echo "  make build-dist      Build distribution packages"
	@echo ""
	@echo "🧹 Clean:"
	@echo "  make clean-artifacts Remove build artifacts and cache"
	@echo "  make clean-venv      Remove virtual environment"
	@echo ""
	@echo "📦 Installation:"
	@echo "  make install-dev     Install with dev dependencies (editable)"
	@echo "  make install-prod    Install in production mode"
	@echo ""
	@echo "✨ Quality:"
	@echo "  make quality-check         Run all quality checks (format + lint + test)"
	@echo "  make quality-format        Format code with black"
	@echo "  make quality-format-check  Check formatting without modifying"
	@echo "  make quality-lint          Run linting (flake8 + mypy)"
	@echo ""
	@echo "🚀 Run Services (using $(CONFIG)):
	@echo "  make serve-all              Launch all services simultaneously"
	@echo "  make 5555-serve-event-flow       Launch Event Flow Visualization (port 5555)"
	@echo "  make 5556-serve-event-recorder   Launch Event Recorder Dashboard (port 5556)"
	@echo "  make 5557-serve-mock-exchange    Launch Mock Exchange Simulator (port 5557)"
	@echo "  make 5558-serve-scenario-testing Launch Scenario Testing Dashboard (port 5558)"
	@echo ""
	@echo "⚙️  Setup:"
	@echo "  make setup-dev       Complete dev setup (venv + install-dev)"
	@echo "  make setup-venv      Create virtual environment"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test-coverage   Run tests with coverage report"
	@echo "  make test-unit       Run tests with pytest"
	@echo ""

# ============================================================================
# BUILD
# ============================================================================

build-dist: clean-artifacts
	@echo "📦 Building distribution packages..."
	$(PYTHON) -m pip install --upgrade build
	$(PYTHON) -m build
	@echo "✅ Build complete! Packages in dist/"

# ============================================================================
# CLEAN
# ============================================================================

clean-artifacts:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf src/*.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "✅ Clean complete!"

clean-venv:
	@echo "🧹 Removing virtual environment..."
	rm -rf $(VENV)
	@echo "✅ Virtual environment removed!"

# ============================================================================
# INSTALLATION
# ============================================================================

install-dev:
	@echo "📦 Installing $(PROJECT_NAME) in development mode..."
	@if [ ! -d "$(VENV)" ]; then \
		make setup-venv; \
	fi
	@. $(VENV)/bin/activate && $(PIP) install --upgrade pip setuptools wheel
	@. $(VENV)/bin/activate && $(PIP) install -e ".[dev]"
	@echo "✅ Development installation complete!"
	@echo ""
	@echo "💡 To use the CLI, either:"
	@echo "   1. Activate venv: source $(VENV)/bin/activate"
	@echo "   2. Use make commands (automatic venv activation)"

install-prod:
	@echo "📦 Installing $(PROJECT_NAME)..."
	@if [ -d "$(VENV)" ]; then \
		. $(VENV)/bin/activate && $(PIP) install .; \
	else \
		$(PIP) install .; \
	fi
	@echo "✅ Installation complete!"

# ============================================================================
# QUALITY
# ============================================================================

quality-check: quality-format-check quality-lint test-unit
	@echo ""
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║                    ✅ All checks passed!                         ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"

quality-format:
	@echo "✨ Formatting code with black..."
	@if [ -d "$(VENV)" ]; then \
		. $(VENV)/bin/activate && black $(PROJECT_PATH) tests/; \
	else \
		black $(PROJECT_PATH) tests/; \
	fi
	@echo "✅ Formatting complete!"

quality-format-check:
	@echo "🔍 Checking code formatting..."
	@if [ -d "$(VENV)" ]; then \
		. $(VENV)/bin/activate && black $(PROJECT_PATH) tests/ --check; \
	else \
		black $(PROJECT_PATH) tests/ --check; \
	fi

quality-lint:
	@echo "🔍 Running flake8..."
	@if [ -d "$(VENV)" ]; then \
		. $(VENV)/bin/activate && flake8 $(PROJECT_PATH) tests/ --max-line-length=100 --exclude=__pycache__,.venv,build,dist; \
	else \
		flake8 $(PROJECT_PATH) tests/ --max-line-length=100 --exclude=__pycache__,.venv,build,dist; \
	fi
	@echo "🔍 Running mypy..."
	@if [ -d "$(VENV)" ]; then \
		. $(VENV)/bin/activate && mypy $(PROJECT_PATH) --ignore-missing-imports; \
	else \
		mypy $(PROJECT_PATH) --ignore-missing-imports; \
	fi
	@echo "✅ Linting complete!"

# ============================================================================
# RUN SERVICES
# ============================================================================

check-config: check-installed
	@if [ ! -f $(CONFIG) ]; then \
		echo "❌ Configuration file not found: $(CONFIG)"; \
		echo ""; \
		echo "💡 Create one with:"; \
		echo "   pubsub-tools config-example -o $(CONFIG)"; \
		exit 1; \
	fi

check-installed:
	@if [ ! -d "$(VENV)" ]; then \
		echo "❌ Virtual environment not found!"; \
		echo ""; \
		echo "💡 Install with:"; \
		echo "   make install-dev"; \
		echo ""; \
		exit 1; \
	fi
	@if ! [ -f "$(VENV)/bin/pubsub-tools" ]; then \
		echo "❌ Package not installed in venv!"; \
		echo ""; \
		echo "💡 Install with:"; \
		echo "   make install-dev"; \
		echo ""; \
		exit 1; \
	fi

serve-all: check-config
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║         🚀 Launching ALL DevTools Services                       ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📊 Event Flow:        http://localhost:5555"
	@echo "🎬 Event Recorder:    http://localhost:5556"
	@echo "🎰 Mock Exchange:     http://localhost:5557"
	@echo "🎯 Scenario Testing:  http://localhost:5558"
	@echo ""
	@echo "⚙️  Config: $(CONFIG)"
	@echo ""
	@echo "Press Ctrl+C to stop all services"
	@echo ""
	@. $(VENV)/bin/activate && pubsub-tools serve-all --config $(CONFIG)

5555-serve-event-flow: check-config
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║         🎯 Launching Event Flow Visualization                    ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📊 Dashboard: http://localhost:5555"
	@echo "⚙️  Config: $(CONFIG)"
	@echo ""
	@. $(VENV)/bin/activate && pubsub-tools event-flow --config $(CONFIG)

5556-serve-event-recorder: check-config
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║          🎬 Launching Event Recorder Dashboard                   ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📊 Dashboard: http://localhost:5556"
	@echo "⚙️  Config: $(CONFIG)"
	@echo ""
	@. $(VENV)/bin/activate && pubsub-tools event-recorder --config $(CONFIG)

5557-serve-mock-exchange: check-config
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║         🎰 Launching Mock Exchange Simulator                     ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📊 Dashboard: http://localhost:5557"
	@echo "⚙️  Config: $(CONFIG)"
	@echo ""
	@. $(VENV)/bin/activate && pubsub-tools mock-exchange --config $(CONFIG)

5558-serve-scenario-testing: check-config
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║        🎯 Launching Scenario Testing Dashboard                   ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📊 Dashboard: http://localhost:5558"
	@echo "⚙️  Config: $(CONFIG)"
	@echo ""
	@. $(VENV)/bin/activate && pubsub-tools scenario-testing --config $(CONFIG)

# ============================================================================
# SETUP
# ============================================================================

setup-dev: setup-venv
	@echo "🔧 Setting up development environment..."
	@. $(VENV)/bin/activate && $(PIP) install --upgrade pip setuptools wheel
	@. $(VENV)/bin/activate && $(PIP) install -e ".[dev]"
	@echo "✅ Development environment ready!"
	@echo "   Activate with: source $(VENV)/bin/activate"

setup-venv:
	@echo "📦 Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "✅ Virtual environment created!"
	@echo "   Activate with: source $(VENV)/bin/activate"

# ============================================================================
# TESTING
# ============================================================================


test-coverage:
	@echo "🧪 Running tests with coverage..."
	@if [ -d "$(VENV)" ]; then \
		. $(VENV)/bin/activate && pytest tests/ --cov=$(PROJECT_PATH) --cov-report=html --cov-report=term-missing -v; \
	else \
		pytest tests/ --cov=$(PROJECT_PATH) --cov-report=html --cov-report=term-missing -v; \
	fi
	@echo "✅ Coverage report: htmlcov/index.html"

test-unit:
	@echo "🧪 Running tests..."
	@if [ -d "$(VENV)" ]; then \
		. $(VENV)/bin/activate && pytest tests/ -v; \
	else \
		pytest tests/ -v; \
	fi
