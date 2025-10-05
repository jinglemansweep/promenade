# Promenade

A powerful, customizable CLI dashboard for Prometheus metrics built with Python and Textual.

## Features

- 📊 **Grid-based Layout**: Flexible grid system for organizing widgets
- 🎨 **Conditional Formatting**: Dynamic styling based on metric values
- 🔄 **Auto-refresh**: Configurable refresh intervals per widget
- 🎯 **Custom Queries**: Full PromQL support
- 🌈 **Theme Support**: Respects Textual themes
- ⚡ **Fast & Lightweight**: Built on Textual framework
- 📝 **YAML Configuration**: Simple, declarative dashboard definitions

## Requirements

- Python 3.12+
- Prometheus server

## Installation

### Using UV (Recommended)

```bash
# Create virtual environment
uv venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/macOS
# or
.venv\Scripts\activate  # On Windows

# Install the package
uv pip install -e .
```

### Using pip

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install the package
pip install -e .
```

### Development Installation

```bash
# Install with development dependencies
uv pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

## Quick Start

1. **Start your Prometheus server** (if not already running)

2. **Create a dashboard configuration** (see `examples/simple.yaml`)

3. **Run the dashboard**:

```bash
# Using environment variable
export PROMETHEUS_URL=http://localhost:9090
promenade examples/simple.yaml

# Or using command-line argument
promenade examples/simple.yaml --prometheus-url http://localhost:9090
```

## Configuration

### Dashboard YAML Format

```yaml
title: "My Dashboard"
grid_rows: 3        # Number of rows in the grid
grid_columns: 3     # Number of columns in the grid

widgets:
  - label: "CPU Usage"                    # Optional widget label
    query: "100 - (avg(rate(...)) * 100)" # PromQL query
    refresh_interval: 5                    # Refresh every 5 seconds
    format_string: "{value:.1f}%"         # Python format string
    row: 0                                 # Grid position (0-indexed)
    column: 0
    row_span: 1                            # Span multiple rows/columns
    column_span: 1
    border_style: "rounded"                # Border style
    conditional_formats:                   # Conditional formatting rules
      - condition: "value > 80"
        border_color: "red"
        text_color: "red"
```

### Widget Configuration

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `label` | string | No | - | Widget label/title |
| `query` | string | Yes | - | PromQL query to execute |
| `refresh_interval` | integer | No | 5 | Refresh interval in seconds |
| `format_string` | string | No | `{value}` | Python format string for display |
| `row` | integer | Yes | - | Row position (0-indexed) |
| `column` | integer | Yes | - | Column position (0-indexed) |
| `row_span` | integer | No | 1 | Number of rows to span |
| `column_span` | integer | No | 1 | Number of columns to span |
| `border_style` | string | No | `solid` | Border style: `none`, `solid`, `dashed`, `double`, `heavy`, `rounded` |
| `conditional_formats` | array | No | [] | List of conditional formatting rules |

### Conditional Formatting

Conditional formats are evaluated in order and applied when their condition is met:

```yaml
conditional_formats:
  - condition: "value > 80"           # Python expression with 'value' variable
    border_color: "red"                # CSS color name or hex code
    text_color: "red"
    background_color: "#ff0000"
    visible: true                      # Control widget visibility
```

**Available condition expressions:**
- Numeric comparisons: `value > 80`, `value <= 50`
- Complex logic: `value > 50 and value < 80`
- Any valid Python expression with `value` variable

**Color options:**
- CSS color names: `red`, `green`, `blue`, `yellow`, etc.
- Hex codes: `#ff0000`, `#00ff00`
- Textual theme colors: `$primary`, `$secondary`, `$text`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PROMETHEUS_URL` | Prometheus server URL | - |
| `PROMETHEUS_TIMEOUT` | Request timeout in seconds | 10 |

## CLI Usage

```bash
promenade [OPTIONS] CONFIG_FILE

Arguments:
  CONFIG_FILE  Path to YAML dashboard configuration

Options:
  -u, --prometheus-url TEXT  Prometheus server URL
  -t, --theme TEXT          Textual theme (default: textual-dark)
  -h, --help                Show help message
```

### Keyboard Shortcuts

- `q` - Quit the application
- `r` - Refresh all metrics immediately

## Examples

See the `examples/` directory for sample configurations:

- `simple.yaml` - Basic dashboard with 3 widgets
- `dashboard.yaml` - Advanced dashboard with conditional formatting

### Example: System Monitoring Dashboard

```yaml
title: "System Monitor"
grid_rows: 2
grid_columns: 2

widgets:
  - label: "CPU %"
    query: "100 - (avg(rate(node_cpu_seconds_total{mode='idle'}[5m])) * 100)"
    refresh_interval: 5
    format_string: "{value:.1f}%"
    row: 0
    column: 0
    conditional_formats:
      - condition: "value > 80"
        border_color: "red"
        text_color: "red"

  - label: "Memory %"
    query: "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100"
    refresh_interval: 5
    format_string: "{value:.1f}%"
    row: 0
    column: 1
    conditional_formats:
      - condition: "value > 90"
        border_color: "red"

  - label: "Active Connections"
    query: "sum(nginx_connections_active)"
    refresh_interval: 3
    format_string: "{value:.0f}"
    row: 1
    column: 0
    row_span: 1
    column_span: 2
```

## Development

### Project Structure

```
promenade/
├── src/promenade/
│   ├── __init__.py
│   ├── cli.py           # CLI entrypoint
│   ├── app.py           # Main Textual application
│   ├── config.py        # Configuration loader
│   ├── schema.py        # Pydantic models
│   ├── prometheus.py    # Prometheus client
│   └── widgets.py       # Custom Textual widgets
├── examples/            # Example dashboards
├── pyproject.toml       # Project configuration
└── README.md
```

### Running Tests

```bash
# Install test dependencies
uv pip install -e ".[dev]"

# Run tests
pytest
```

### Code Quality

```bash
# Run linter
ruff check .

# Run formatter
ruff format .

# Run type checker
mypy src/
```

## Troubleshooting

### Connection Issues

If you see connection errors:
1. Verify Prometheus is running: `curl http://localhost:9090/api/v1/query?query=up`
2. Check the Prometheus URL is correct
3. Ensure there are no firewall restrictions

### Query Errors

If widgets show "No data":
1. Test your query in Prometheus UI
2. Verify metric names exist
3. Check query syntax in PromQL

### Display Issues

If widgets overlap or don't fit:
1. Check `grid_rows` and `grid_columns` match your layout
2. Verify `row + row_span <= grid_rows`
3. Verify `column + column_span <= grid_columns`

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [Textual](https://textual.textualize.io/)
- Inspired by Prometheus monitoring needs
- Thanks to the Python community
