"""Main Textual application for the Prometheus dashboard."""

from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.widgets import Footer, Header

from promenade.prometheus import PrometheusClient
from promenade.schema import DashboardConfig
from promenade.widgets import MetricWidget


class PrometheusDashboard(App):  # type: ignore[misc]
    """A Textual app for displaying Prometheus metrics."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #dashboard-grid {
        width: 100%;
        height: 1fr;
        grid-size: 1 1;  /* Will be set dynamically */
        grid-gutter: 1;
        padding: 1;
    }

    .empty-cell {
        width: 0;
        height: 0;
        visibility: hidden;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    def __init__(
        self,
        config: DashboardConfig,
        prometheus_client: PrometheusClient,
        *args: object,
        **kwargs: object,
    ) -> None:
        """Initialize the dashboard app.

        Args:
            config: Dashboard configuration
            prometheus_client: Prometheus client for queries
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.config = config
        self.prometheus_client = prometheus_client
        self.title = config.title
        self.sub_title = "Promenade"

    def compose(self) -> ComposeResult:
        """Compose the app's widgets."""
        from textual.widgets import Static

        yield Header()

        # Create a 2D grid to hold widgets
        # We'll use a placeholder-based approach
        grid_cells: list[list[MetricWidget | Static | str | None]] = [
            [None] * self.config.grid_columns for _ in range(self.config.grid_rows)
        ]

        # Place widgets in the grid based on their configuration
        for widget_config in self.config.widgets:
            metric_widget = MetricWidget(config=widget_config)

            # Set span on the widget
            metric_widget.styles.column_span = widget_config.column_span
            metric_widget.styles.row_span = widget_config.row_span

            # Mark cells as occupied by this widget
            for r in range(widget_config.row, widget_config.row + widget_config.row_span):
                for c in range(
                    widget_config.column, widget_config.column + widget_config.column_span
                ):
                    if r < self.config.grid_rows and c < self.config.grid_columns:
                        if r == widget_config.row and c == widget_config.column:
                            grid_cells[r][c] = metric_widget
                        else:
                            # Mark as occupied but don't place widget
                            grid_cells[r][c] = "occupied"

        # Create grid with all cells
        with Grid(id="dashboard-grid"):
            for row in grid_cells:
                for cell in row:
                    if isinstance(cell, MetricWidget):
                        yield cell
                    elif cell is None:
                        # Empty cell - add a placeholder
                        placeholder = Static("", classes="empty-cell")
                        placeholder.styles.visibility = "hidden"
                        yield placeholder

        yield Footer(show_command_palette=False)

    def on_mount(self) -> None:
        """Configure grid and start refresh timer after mounting."""
        grid = self.query_one("#dashboard-grid", Grid)
        grid.styles.grid_size_columns = self.config.grid_columns
        grid.styles.grid_size_rows = self.config.grid_rows

        # Start the dashboard-level refresh
        self.refresh_all_metrics()
        self.set_interval(self.config.refresh_interval, self.refresh_all_metrics)

    def refresh_all_metrics(self) -> None:
        """Fetch all metrics from Prometheus in a batch and update widgets."""
        # Collect all unique queries
        queries = [widget.query for widget in self.config.widgets]

        # Execute batch query
        results = self.prometheus_client.query_batch(queries)

        # Update each widget with its result
        for widget_element in self.query(MetricWidget):
            query = widget_element.config.query
            value = results.get(query)
            widget_element.update_value(value)

    def action_refresh_all(self) -> None:
        """Manually refresh all metrics immediately."""
        self.refresh_all_metrics()

    def on_unmount(self) -> None:
        """Clean up when the app is closed."""
        self.prometheus_client.close()
