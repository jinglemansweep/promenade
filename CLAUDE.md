# Promenade - Developer Guide for Claude

This document provides context and guidance for AI assistants (like Claude) working on the Promenade project.

## Project Overview

Promenade is a powerful, customizable CLI dashboard for Prometheus metrics built with Python and Textual. It provides a terminal-based grid layout system for displaying real-time metrics with conditional formatting and auto-refresh capabilities.

## Tech Stack

- **Python 3.12+**: Core language
- **Textual**: TUI (Terminal User Interface) framework for building the dashboard
- **Pydantic**: Data validation and settings management
- **Click**: Command-line interface creation
- **PyYAML**: YAML configuration parsing
- **Requests**: HTTP client for Prometheus API
- **UV**: Fast Python package installer and resolver (recommended)

## Project Structure

```
promenade/
├── src/promenade/
│   ├── __init__.py       # Package initialization
│   ├── cli.py            # CLI entrypoint using Click
│   ├── app.py            # Main Textual application and dashboard logic
│   ├── config.py         # Configuration loader for YAML files
│   ├── schema.py         # Pydantic models for validation
│   ├── prometheus.py     # Prometheus API client
│   └── widgets.py        # Custom Textual widgets for metrics display
├── examples/             # Example dashboard configurations
│   └── simple.yaml       # Sample dashboard config
├── .pre-commit-config.yaml  # Pre-commit hooks configuration
├── pyproject.toml        # Project metadata and dependencies
├── uv.lock               # UV lock file for reproducible installs
└── README.md             # User-facing documentation
```

## Development Setup

### Quick Start

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd promenade

# Install dependencies using UV (recommended)
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Activate virtual environment (UV creates .venv automatically)
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows
```

### Running the Application

```bash
# Set Prometheus URL
export PROMETHEUS_URL=http://localhost:9090

# Run with example config
uv run promenade examples/simple.yaml

# Or with explicit URL
uv run promenade examples/simple.yaml --prometheus-url http://localhost:9090
```

## Code Quality Tools

The project uses several tools to maintain code quality:

### Ruff (Linter & Formatter)

```bash
# Check for linting issues
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

Configuration in `pyproject.toml`:
- Line length: 100 characters
- Target: Python 3.12
- Selected rules: E (errors), F (pyflakes), I (isort), N (naming), W (warnings), B (bugbear), Q (quotes)

### MyPy (Type Checker)

```bash
# Run type checking
uv run mypy src/
```

Configuration in `pyproject.toml`:
- Strict mode enabled
- All functions must have type annotations
- Warns on unused configs and any returns

### Pre-commit Hooks

The project uses pre-commit hooks that run automatically on `git commit`:

1. **Basic checks**: trailing whitespace, end-of-file fixer, YAML/TOML validation
2. **Ruff**: Auto-formatting and linting
3. **MyPy**: Type checking

Run manually:
```bash
# Run on all files
uv run pre-commit run --all-files

# Run on staged files only
uv run pre-commit run
```

## Key Components

### 1. Configuration System (`config.py`, `schema.py`)

- Uses Pydantic models for validation
- Loads YAML dashboard configurations
- Key models:
  - `DashboardConfig`: Top-level dashboard configuration
  - `WidgetConfig`: Individual widget settings
  - `ConditionalFormat`: Conditional styling rules

### 2. Prometheus Client (`prometheus.py`)

- Handles communication with Prometheus API
- Executes PromQL queries
- Environment variables:
  - `PROMETHEUS_URL`: Server URL (required)
  - `PROMETHEUS_TIMEOUT`: Request timeout (default: 10s)

### 3. Textual Application (`app.py`, `widgets.py`)

- `PrometheusDashboard`: Main Textual app
- Custom widgets for metric display
- Grid-based layout system
- Auto-refresh mechanism with configurable intervals
- Keyboard shortcuts:
  - `q`: Quit
  - `r`: Refresh all metrics

### 4. CLI Interface (`cli.py`)

- Uses Click for command-line parsing
- Accepts config file path as argument
- Options for Prometheus URL and theme selection

## Common Development Tasks

### Adding a New Widget Type

1. Define widget class in `widgets.py` (inherit from Textual's `Widget` or `Static`)
2. Add configuration fields to `WidgetConfig` in `schema.py`
3. Update widget rendering logic in `app.py`
4. Update README documentation

### Adding Configuration Options

1. Add fields to appropriate Pydantic model in `schema.py`
2. Update YAML loading in `config.py` if needed
3. Update widget/app logic to use new options
4. Add examples to `examples/` directory
5. Document in README.md

### Modifying Prometheus Integration

1. Update client methods in `prometheus.py`
2. Ensure proper error handling
3. Update type hints
4. Test with actual Prometheus server

## Testing

While the project currently doesn't have a test suite, when adding tests:

```bash
# Install with dev dependencies
uv sync

# Run tests (when implemented)
uv run pytest

# Run with coverage
uv run pytest --cov=promenade
```

## Common Patterns

### Error Handling

- Use Click's error output: `click.echo(f"Error: {e}", err=True)`
- Exit with appropriate status codes
- Provide helpful error messages

### Type Hints

- All functions must have type hints (enforced by mypy)
- Use modern Python type syntax: `str | None` instead of `Optional[str]`
- Import from `typing` when needed

### Code Style

- Follow PEP 8 (enforced by Ruff)
- Use descriptive variable names
- Add docstrings to functions and classes
- Keep functions focused and single-purpose

## Debugging Tips

### Textual Development

```bash
# Run with Textual devtools for debugging
textual console
# In another terminal:
uv run promenade examples/simple.yaml
```

### Prometheus Queries

Test queries directly in Prometheus UI before adding to config:
```
http://localhost:9090/graph
```

### Configuration Issues

Validate YAML syntax:
```bash
python -c "import yaml; yaml.safe_load(open('examples/simple.yaml'))"
```

## Dependencies Management

### Adding Dependencies

```bash
# Add a runtime dependency
uv add <package-name>

# Add a dev dependency
uv add --dev <package-name>

# Sync dependencies after manual pyproject.toml edits
uv sync
```

### Updating Dependencies

```bash
# Update all dependencies
uv lock --upgrade

# Update specific package
uv lock --upgrade-package <package-name>

# Sync after updating
uv sync
```

## Git Workflow

1. Create feature branch from main
2. Make changes
3. Run pre-commit checks: `uv run pre-commit run --all-files`
4. Commit with descriptive messages
5. Push and create pull request

## Current Limitations & Future Work

- No automated tests yet (pytest infrastructure in place)
- Limited widget types (currently only metric display)
- No persistent storage of dashboard state
- Single dashboard per instance
- No authentication for Prometheus connection

## Resources

- [Textual Documentation](https://textual.textualize.io/)
- [Prometheus Query Documentation](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [UV Documentation](https://github.com/astral-sh/uv)
- [Ruff Documentation](https://docs.astral.sh/ruff/)

## License

MIT License - See LICENSE file for details
