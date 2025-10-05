"""Configuration loader for dashboard YAML files."""

from pathlib import Path

import yaml

from promenade.schema import DashboardConfig


def load_dashboard_config(file_path: str | Path) -> DashboardConfig:
    """Load and parse a dashboard configuration from a YAML file.

    Args:
        file_path: Path to the YAML configuration file

    Returns:
        Parsed dashboard configuration

    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        yaml.YAMLError: If the YAML is invalid
        pydantic.ValidationError: If the configuration doesn't match the schema
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")

    with path.open("r") as f:
        data = yaml.safe_load(f)

    return DashboardConfig.model_validate(data)
