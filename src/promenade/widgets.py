"""Custom Textual widgets for displaying Prometheus metrics."""

from collections import deque
from typing import Any

from textual.app import ComposeResult
from textual.color import Color
from textual.containers import Container
from textual.widgets import Digits, Label, ProgressBar, Sparkline, Static

from promenade.schema import ConditionalFormat, WidgetConfig, WidgetType


class MetricWidget(Container):  # type: ignore[misc]
    """A widget that displays a Prometheus metric with conditional formatting."""

    DEFAULT_CSS = """
    MetricWidget {
        border: heavy $secondary;
        border-title-color: $text;
        border-subtitle-color: $primary;
        height: auto;
        padding: 0 1;
    }

    MetricWidget > .metric-label {
        text-style: bold;
    }

    MetricWidget > .metric-value {
        content-align: center middle;
        text-align: center;
        height: 1fr;
    }

    MetricWidget > ProgressBar {
        height: 1;
        align: center middle;
    }

    MetricWidget > .value-text {
        text-align: center;
        height: auto;
        margin-top: 1;
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
        self._value_widget: Static | Digits | ProgressBar | Sparkline | None = None
        self._value_text: Static | None = None  # Text display for sparkline/progress

        # For sparkline: keep historical data
        self._sparkline_data: deque[float] = deque(maxlen=config.sparkline_data_points)

        # Set border style
        self.border_title = config.title or ""
        if config.subtitle:
            self.border_subtitle = f"[right]{config.subtitle}[/right]"
        if config.border_style.value != "none":
            self.border = config.border_style.value

    def compose(self) -> ComposeResult:
        """Compose the widget's child widgets."""
        # Create the appropriate widget type based on configuration
        if self.config.type == WidgetType.DIGITS:
            self._value_widget = Digits("---", classes="metric-value")
            yield self._value_widget
        elif self.config.type == WidgetType.SPARKLINE:
            self._value_widget = Sparkline(
                data=[0.0], summary_function=self._get_summary_function(), classes="metric-value"
            )
            yield self._value_widget
            # Add text label below sparkline to show formatted value
            self._value_text = Static("Loading...", classes="value-text")
            yield self._value_text
        elif self.config.type == WidgetType.PROGRESS:
            total = self.config.progress_total or 100.0
            self._value_widget = ProgressBar(
                total=total,
                show_percentage=self.config.show_percentage,
                show_eta=self.config.show_eta,
                classes="metric-value",
            )
            yield self._value_widget
            # Add text label below progress bar to show formatted value
            self._value_text = Static("Loading...", classes="value-text")
            yield self._value_text
        else:  # TEXT (default)
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
                self._update_widget_display("No data")
            elif isinstance(value, str) and value.startswith("Error:"):
                self._update_widget_display(value)
            else:
                # Update widget based on type
                if self.config.type == WidgetType.SPARKLINE:
                    self._update_sparkline(value)
                elif self.config.type == WidgetType.PROGRESS:
                    self._update_progress(value)
                elif self.config.type == WidgetType.DIGITS:
                    display_text = self._format_value(value)
                    if isinstance(self._value_widget, Digits):
                        self._value_widget.update(display_text)
                else:  # TEXT
                    display_text = self._format_value(value)
                    self._update_widget_display(display_text)

            # Apply conditional formatting
            self._apply_conditional_formatting(value)

        except Exception as e:
            self._update_widget_display(f"Error: {str(e)}")
            self.current_value = None

    def _update_widget_display(self, text: str) -> None:
        """Update the display text for text-based widgets."""
        if isinstance(self._value_widget, (Static, Digits)):
            self._value_widget.update(text)

    def _update_sparkline(self, value: Any) -> None:
        """Update sparkline with new data point."""
        try:
            numeric_value = float(value)
            self._sparkline_data.append(numeric_value)

            if isinstance(self._value_widget, Sparkline):
                # Update sparkline data
                self._value_widget.data = list(self._sparkline_data)

            # Update text label with formatted value
            if self._value_text:
                display_text = self._format_value(value)
                self._value_text.update(display_text)
        except (ValueError, TypeError):
            if self._value_text:
                self._value_text.update("Error")

    def _update_progress(self, value: Any) -> None:
        """Update progress bar with new value."""
        try:
            numeric_value = float(value)

            if isinstance(self._value_widget, ProgressBar):
                if self.config.progress_total is not None:
                    # Value is absolute, update progress
                    self._value_widget.update(progress=numeric_value)
                else:
                    # Value is a percentage (0-100), update accordingly
                    self._value_widget.update(progress=numeric_value)

            # Update text label with formatted value
            if self._value_text:
                display_text = self._format_value(value)
                self._value_text.update(display_text)
        except (ValueError, TypeError):
            if self._value_text:
                self._value_text.update("Error")

    def _get_summary_function(self) -> Any:
        """Get the summary function for sparkline based on config."""
        summary_map = {
            "max": max,
            "min": min,
            "mean": lambda x: sum(x) / len(x) if x else 0,
        }
        return summary_map.get(self.config.sparkline_summary, max)

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

    def _resolve_color(self, color_str: str) -> Color | str:
        """Resolve a color string, handling both regular colors and theme variables.

        Args:
            color_str: Color string (can be a theme variable like $success, $error, etc.)

        Returns:
            Resolved color string or Color object
        """
        # If it's a theme variable (starts with $), get it from the theme
        # DO NOT adjust theme variables - they're already designed for the current theme!
        if color_str.startswith("$"):
            try:
                # Get the design system
                design = self.app.design
                var_name = color_str[1:].replace("-", "_")  # Remove $ and convert dashes

                # Try to get from design.variables
                if hasattr(design, "variables") and hasattr(design.variables, var_name):
                    color = getattr(design.variables, var_name)
                    if isinstance(color, Color):
                        return color  # Return theme color as-is!
                    return Color.parse(str(color))

                # If not found in variables, try common theme color names directly
                # These are the standard Textual theme variables
                if hasattr(design, var_name):
                    color = getattr(design, var_name)
                    if isinstance(color, Color):
                        return color
                    return Color.parse(str(color))

            except Exception:
                pass  # Fall through to fallback

            # Fallback if theme variable not found: use sensible defaults
            # that match typical theme colors
            fallback_map = {
                "success": "lime",
                "error": "red",
                "warning": "yellow",
                "primary": "dodgerblue",
                "secondary": "purple",
                "accent": "cyan",
            }

            var_name = color_str[1:].replace("-", "_")
            if var_name in fallback_map:
                # Use fallback color and adjust it for theme
                color_str = fallback_map[var_name]
                # Fall through to adjustment logic below
            else:
                # Unknown variable, return as-is
                return color_str

        # Otherwise, adjust the color for the current theme
        try:
            # Parse the color
            color = Color.parse(color_str)

            # Check theme name first (most reliable)
            theme_name = str(getattr(self.app, "theme", "textual-dark"))
            is_light_theme = "light" in theme_name.lower()

            # Adjust color based on theme
            if is_light_theme:
                # Light theme - need much darker colors for visibility
                # For very bright colors like lime, yellow, cyan - darken heavily
                luminance = (0.299 * color.r + 0.587 * color.g + 0.114 * color.b) / 255.0

                if luminance > 0.7:  # Very bright colors (lime, yellow, cyan, etc.)
                    adjusted = color.darken(0.7)  # Darken by 70%
                elif luminance > 0.5:  # Medium bright colors
                    adjusted = color.darken(0.5)  # Darken by 50%
                else:  # Already darker colors (red, blue, etc.)
                    adjusted = color.darken(0.3)  # Darken by 30%
            else:
                # Dark theme - brighten the color moderately
                adjusted = color.lighten(0.3)

            return adjusted

        except Exception:
            # If anything goes wrong, return original color
            return color_str

    def _apply_format(self, fmt: ConditionalFormat) -> None:
        """Apply a conditional format to the widget.

        Args:
            fmt: Conditional format to apply
        """
        if fmt.text_color and self._value_widget:
            resolved_color = self._resolve_color(fmt.text_color)
            self._value_widget.styles.color = resolved_color

        if fmt.background_color and self._value_widget:
            resolved_color = self._resolve_color(fmt.background_color)
            self._value_widget.styles.background = resolved_color

        if fmt.border_color:
            # Resolve border color (handles theme variables and regular colors)
            resolved_color = self._resolve_color(fmt.border_color)
            # Border format: (style, color) or just style
            self.styles.border = (self.config.border_style.value, resolved_color)

        if fmt.visible is not None:
            self.display = fmt.visible
