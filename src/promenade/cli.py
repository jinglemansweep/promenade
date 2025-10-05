"""CLI entrypoint for the Promenade dashboard."""

import sys
from pathlib import Path

import click

from promenade.app import PrometheusDashboard
from promenade.config import load_dashboard_config
from promenade.prometheus import create_prometheus_client_from_env


@click.command()  # type: ignore[misc]
@click.argument(  # type: ignore[misc]
    "config_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)
@click.option(  # type: ignore[misc]
    "--prometheus-url",
    "-u",
    envvar="PROMETHEUS_URL",
    help="Prometheus server URL (can also use PROMETHEUS_URL env var)",
)
@click.option(  # type: ignore[misc]
    "--theme",
    "-t",
    default="textual-dark",
    help="Textual theme to use (default: textual-dark)",
)
def main(
    config_file: Path,
    prometheus_url: str | None,
    theme: str,
) -> None:
    """Launch the Prometheus dashboard with the specified configuration.

    CONFIG_FILE: Path to the YAML dashboard configuration file.

    Environment variables:
      PROMETHEUS_URL: Prometheus server URL (e.g., http://localhost:9090)
      PROMETHEUS_TIMEOUT: Request timeout in seconds (default: 10)
    """
    try:
        # Load dashboard configuration
        config = load_dashboard_config(config_file)

        # Create Prometheus client
        prometheus_client = create_prometheus_client_from_env(prometheus_url)

        # Create and run the app
        app = PrometheusDashboard(
            config=config,
            prometheus_client=prometheus_client,
        )

        # Set theme if provided
        if theme:
            app.theme = theme

        app.run()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
