# Contributing to Python PubSub DevTools

## Development Setup

This project depends on local packages that need to be installed in editable mode.

### Local Dependencies

The project has two local dependencies that are **not published to PyPI**:

- `python-pubsub-client` (located in `../../venantvr-pubsub/Python.PubSub.Client`)
- `python-pubsub-devtools-consumers` (located in `../../venantvr-pubsub/Python.PubSub.DevTools.Consumers`)

These dependencies are automatically installed in **editable mode** (`-e`) when you run the development setup.

### Installation

```bash
# Complete development setup (recommended)
make setup-dev

# Or, if you already have a venv:
make install-dev
```

This will:

1. Create a virtual environment (if needed)
2. Install local dependencies in editable mode from `requirements-dev.txt`
3. Install this package in editable mode with dev dependencies

### Why Use requirements-dev.txt?

The `requirements-dev.txt` file is used for local dependencies in editable mode because:

- `pyproject.toml` cannot contain `-e` flags (not PEP 508 compliant)
- Editable installs allow you to modify the source code of dependencies and see changes immediately
- The Makefile automatically handles the installation order

### Verifying Installation

Check that the local packages are installed in editable mode:

```bash
pip list | grep -E "python-pubsub-client|python-pubsub-devtools-consumers"
```

You should see:

```
python-pubsub-client             0.1.0    /path/to/Python.PubSub.Client/src
python-pubsub-devtools-consumers 0.1.0    /path/to/Python.PubSub.DevTools.Consumers/src
```

## Running Tests

```bash
# Run unit tests
make test

# Run with coverage
make test-coverage
```

## Code Quality

```bash
# Format code
make quality-format

# Run linting
make quality-lint

# Run all checks (format + lint + tests)
make quality-check
```
