"""Custom Textual widgets for displaying Prometheus metrics."""

from typing import Any

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Label, Static

from promenade.schema import ConditionalFormat, WidgetConfig


class MetricWidget(Container):  # type: ignore[misc]
    """A widget that displays a Prometheus metric with conditional formatting."""

    DEFAULT_CSS = """
    MetricWidget {
        border: solid;
        height: auto;
        padding: 1;
    }

    MetricWidget > .metric-label {
        text-style: bold;
    }

    MetricWidget > .metric-value {
        content-align: center middle;
        height: 1fr;
    }
    """

    def __init__(
        self,
        config: WidgetConfig,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the metric widget.

        Args:
            config: Widget configuration
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.config = config
        self.current_value: Any = None
        self._label_widget: Label | None = None
        self._value_widget: Static | None = None

        # Set border style
        self.border_title = config.label or ""
        if config.border_style.value != "none":
            self.border = config.border_style.value

    def compose(self) -> ComposeResult:
        """Compose the widget's child widgets."""
        self._value_widget = Static("Loading...", classes="metric-value")
        yield self._value_widget

    def update_value(self, value: Any) -> None:
        """Update the widget with a new value.

        Args:
            value: The metric value to display
        """
        try:
            self.current_value = value

            if value is None:
                display_text = "No data"
            elif isinstance(value, str) and value.startswith("Error:"):
                display_text = value
            else:
                # Try to format the value
                display_text = self._format_value(value)

            if self._value_widget:
                self._value_widget.update(display_text)

            # Apply conditional formatting
            self._apply_conditional_formatting(value)

        except Exception as e:
            if self._value_widget:
                self._value_widget.update(f"Error: {str(e)}")
            self.current_value = None

    def _format_value(self, value: Any) -> str:
        """Format a value for display.

        Supports both standard format strings and Python expressions.

        Args:
            value: The value to format

        Returns:
            Formatted string
        """
        format_string = self.config.format_string

        # Check if it's a Python expression (contains quotes and conditional)
        if "'" in format_string or '"' in format_string:
            try:
                # Convert value to appropriate type
                try:
                    numeric_value = float(value)
                except (ValueError, TypeError):
                    numeric_value = value

                # Evaluate as Python expression with safe namespace
                namespace = {
                    "value": numeric_value,
                    "__builtins__": {},
                }
                result = eval(format_string, namespace)
                return str(result)
            except Exception:
                # Fall back to standard formatting
                pass

        # Standard format string
        try:
            numeric_value = float(value)
            return format_string.format(value=numeric_value)
        except (ValueError, TypeError):
            return format_string.format(value=value)

    def _apply_conditional_formatting(self, value: Any) -> None:
        """Apply conditional formatting rules based on the current value.

        Args:
            value: The current metric value
        """
        # Reset to default styles - Textual will use theme colors when reset
        if self._value_widget:
            # Reset color and background by setting to None
            self._value_widget.styles.color = None
            self._value_widget.styles.background = None

        # Reset border to default (set to None to use the border set in __init__)
        self.styles.border = None
        self.display = True

        if value is None:
            return

        # Evaluate each conditional format
        for fmt in self.config.conditional_formats:
            try:
                # Create a safe evaluation context
                condition_met = self._evaluate_condition(fmt.condition, value)

                if condition_met:
                    self._apply_format(fmt)

            except Exception:
                # Silently ignore invalid conditions
                pass

    def _evaluate_condition(self, condition: str, value: Any) -> bool:
        """Safely evaluate a condition expression.

        Args:
            condition: Python expression to evaluate
            value: Current metric value

        Returns:
            True if condition is met, False otherwise
        """
        try:
            # Convert value to float if possible for numeric comparisons
            try:
                numeric_value = float(value)
            except (ValueError, TypeError):
                numeric_value = value

            # Create a restricted namespace for evaluation
            namespace = {
                "value": numeric_value,
                "__builtins__": {},
            }

            return bool(eval(condition, namespace))
        except Exception:
            return False

    def _apply_format(self, fmt: ConditionalFormat) -> None:
        """Apply a conditional format to the widget.

        Args:
            fmt: Conditional format to apply
        """
        if fmt.text_color and self._value_widget:
            self._value_widget.styles.color = fmt.text_color

        if fmt.background_color and self._value_widget:
            self._value_widget.styles.background = fmt.background_color

        if fmt.border_color:
            # Border format: (style, color) or just style
            self.styles.border = (self.config.border_style.value, fmt.border_color)
            # Also set the border title color for visibility
            self.styles.border_title_color = "white"

        if fmt.visible is not None:
            self.display = fmt.visible
