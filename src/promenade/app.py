"""Main Textual application for the Prometheus dashboard."""

from textual.app import App, ComposeResult
from textual.containers import Grid, VerticalScroll
from textual.widgets import Footer, Header, Static

from promenade.prometheus import PrometheusClient
from promenade.schema import DashboardConfig
from promenade.widgets import MetricWidget


class DashboardView(VerticalScroll):  # type: ignore[misc]
    """A view displaying a single dashboard configuration."""

    CSS = """
    DashboardView {
        height: 1fr;
    }

    #dashboard-grid {
        width: 100%;
        height: auto;
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

    def __init__(
        self,
        config: DashboardConfig,
        prometheus_client: PrometheusClient,
        *args: object,
        **kwargs: object,
    ) -> None:
        """Initialize the dashboard view.

        Args:
            config: Dashboard configuration
            prometheus_client: Prometheus client for queries
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.config = config
        self.prometheus_client = prometheus_client

    def compose(self) -> ComposeResult:
        """Compose the view's widgets."""
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

    def on_mount(self) -> None:
        """Configure grid after mounting."""
        grid = self.query_one("#dashboard-grid", Grid)
        grid.styles.grid_size_columns = self.config.grid_columns
        grid.styles.grid_size_rows = self.config.grid_rows

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


class PrometheusDashboard(App):  # type: ignore[misc]
    """A Textual app for displaying Prometheus metrics with carousel navigation."""

    CSS = """
    Screen {
        layout: vertical;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("left,n", "previous_screen", "Previous"),
        ("right,m", "next_screen", "Next"),
    ]

    def __init__(
        self,
        configs: list[DashboardConfig],
        prometheus_client: PrometheusClient,
        *args: object,
        **kwargs: object,
    ) -> None:
        """Initialize the dashboard app.

        Args:
            configs: List of dashboard configurations
            prometheus_client: Prometheus client for queries
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.configs = configs
        self.prometheus_client = prometheus_client
        self.current_dashboard_index = 0
        self.sub_title = "Promenade"
        self.dashboard_views: list[DashboardView] = []
        self._refresh_timer_id: int | None = None

    def compose(self) -> ComposeResult:
        """Compose the app's widgets."""
        yield Header()

        # Create all dashboard views
        for config in self.configs:
            view = DashboardView(
                config=config,
                prometheus_client=self.prometheus_client,
            )
            self.dashboard_views.append(view)
            # Only yield the first one initially
            if len(self.dashboard_views) == 1:
                yield view

        yield Footer(show_command_palette=False)

    def on_mount(self) -> None:
        """Start refresh timer after mounting."""
        if self.configs:
            self.title = self.configs[0].title
            self._start_refresh_timer()

    def _start_refresh_timer(self) -> None:
        """Start or restart the refresh timer for current dashboard."""
        # Note: Textual automatically handles timer cleanup, so we just create a new one
        current_config = self.configs[self.current_dashboard_index]
        self._refresh_timer_id = self.set_interval(
            current_config.refresh_interval, self._refresh_current_dashboard
        )
        # Immediately refresh
        self._refresh_current_dashboard()

    def _refresh_current_dashboard(self) -> None:
        """Refresh the currently visible dashboard."""
        if self.dashboard_views:
            self.dashboard_views[self.current_dashboard_index].refresh_all_metrics()

    def action_refresh(self) -> None:
        """Manually refresh all metrics on current dashboard."""
        self._refresh_current_dashboard()

    def _switch_dashboard(self, new_index: int) -> None:
        """Switch to a different dashboard view."""
        if new_index == self.current_dashboard_index or not self.dashboard_views:
            return

        # Get the container (the screen's children between Header and Footer)
        old_view = self.dashboard_views[self.current_dashboard_index]
        new_view = self.dashboard_views[new_index]

        # Remove old view and add new view
        old_view.remove()
        self.mount(new_view, before=self.query_one(Footer))

        # Update state
        self.current_dashboard_index = new_index
        self.title = self.configs[new_index].title

        # Restart refresh timer for new dashboard
        self._start_refresh_timer()

    def action_next_screen(self) -> None:
        """Switch to the next dashboard."""
        if len(self.configs) <= 1:
            return

        new_index = (self.current_dashboard_index + 1) % len(self.configs)
        self._switch_dashboard(new_index)

    def action_previous_screen(self) -> None:
        """Switch to the previous dashboard."""
        if len(self.configs) <= 1:
            return

        new_index = (self.current_dashboard_index - 1) % len(self.configs)
        self._switch_dashboard(new_index)

    def on_unmount(self) -> None:
        """Clean up when the app is closed."""
        self.prometheus_client.close()
