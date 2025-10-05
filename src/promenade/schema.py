"""Schema definitions for dashboard YAML configuration."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class BorderStyle(str, Enum):
    """Available border styles."""

    NONE = "none"
    SOLID = "solid"
    DASHED = "dashed"
    DOUBLE = "double"
    HEAVY = "heavy"
    ROUNDED = "rounded"


class WidgetType(str, Enum):
    """Available widget types."""

    TEXT = "text"
    DIGITS = "digits"
    SPARKLINE = "sparkline"
    PROGRESS = "progress"


class ConditionalFormat(BaseModel):
    """Conditional formatting rules for widgets."""

    condition: str = Field(..., description="Python expression evaluated with 'value' variable")
    border_color: str | None = Field(
        None, description="Border color when condition is true (e.g., 'red', '#ff0000')"
    )
    text_color: str | None = Field(
        None, description="Text color when condition is true (e.g., 'green', '#00ff00')"
    )
    background_color: str | None = Field(
        None, description="Background color when condition is true"
    )
    visible: bool | None = Field(None, description="Widget visibility when condition is true")

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v: str) -> str:
        """Validate that condition is a non-empty string."""
        if not v.strip():
            raise ValueError("Condition cannot be empty")
        return v


class WidgetConfig(BaseModel):
    """Configuration for a single dashboard widget."""

    type: WidgetType = Field(
        WidgetType.TEXT, description="Widget type (text, digits, sparkline, progress)"
    )
    label: str | None = Field(None, description="Optional label for the widget")
    query: str = Field(..., description="Prometheus query to execute")
    format_string: str = Field("{value}", description="Format string for displaying the value")
    row: int = Field(..., description="Row position in grid (0-indexed)", ge=0)
    column: int = Field(..., description="Column position in grid (0-indexed)", ge=0)
    row_span: int = Field(1, description="Number of rows to span", ge=1)
    column_span: int = Field(1, description="Number of columns to span", ge=1)
    border_style: BorderStyle = Field(BorderStyle.SOLID, description="Border style for the widget")
    conditional_formats: list[ConditionalFormat] = Field(
        default_factory=list, description="List of conditional formatting rules"
    )

    # Progress bar specific options
    progress_total: float | None = Field(
        None, description="Total value for progress bar (if None, uses value as percentage)"
    )
    show_percentage: bool = Field(True, description="Show percentage for progress bar")
    show_eta: bool = Field(
        False, description="Show ETA for progress bar (always False for static metrics)"
    )

    # Sparkline specific options
    sparkline_summary: str = Field(
        "max", description="Summary function for sparkline (max, min, mean)"
    )
    sparkline_data_points: int = Field(
        20, description="Number of historical data points to keep for sparkline"
    )


class DashboardConfig(BaseModel):
    """Complete dashboard configuration."""

    title: str = Field("Prometheus Dashboard", description="Dashboard title")
    refresh_interval: int = Field(5, description="Dashboard refresh interval in seconds", ge=1)
    grid_rows: int = Field(..., description="Number of rows in the grid", ge=1)
    grid_columns: int = Field(..., description="Number of columns in the grid", ge=1)
    widgets: list[WidgetConfig] = Field(
        default_factory=list, description="List of widgets to display"
    )

    @field_validator("widgets")
    @classmethod
    def validate_widget_positions(cls, v: list[WidgetConfig], info: Any) -> list[WidgetConfig]:
        """Validate that all widgets fit within the grid."""
        data = info.data
        if "grid_rows" not in data or "grid_columns" not in data:
            return v

        grid_rows = data["grid_rows"]
        grid_columns = data["grid_columns"]

        for widget in v:
            if widget.row + widget.row_span > grid_rows:
                raise ValueError(
                    f"Widget at row {widget.row} with row_span {widget.row_span} "
                    f"exceeds grid_rows {grid_rows}"
                )
            if widget.column + widget.column_span > grid_columns:
                raise ValueError(
                    f"Widget at column {widget.column} with column_span {widget.column_span} "
                    f"exceeds grid_columns {grid_columns}"
                )

        return v
