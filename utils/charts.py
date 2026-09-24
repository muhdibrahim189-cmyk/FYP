"""
Shared Plotly styling. Backgrounds, text and grid colours are left to
Streamlit's Plotly theme so charts follow the light/dark app theme.
"""

from typing import Any

import plotly.graph_objects as go

BLUE = "#2563EB"
AMBER = "#d97706"
RED = "#dc2626"
GREEN = "#16a34a"
PURPLE = "#7c3aed"
ORANGE = "#ea580c"

# CSS-only (not valid in Plotly): heading colour that follows the app theme.
HEADING = "var(--ct-heading)"

SCOPE_COLORS = {1: AMBER, 2: BLUE}
SCOPE_LABEL_COLORS = {"Scope 1": AMBER, "Scope 2": BLUE}

GRID_AXIS = {"showgrid": True, "zeroline": False}

BASE_LAYOUT: dict[str, Any] = {
    "font": {"family": "Inter, sans-serif"},
    "margin": {"t": 45, "b": 25, "l": 10, "r": 10},
    "xaxis": GRID_AXIS,
    "yaxis": GRID_AXIS,
}


def apply_layout(fig: go.Figure, height: int, **overrides: Any) -> go.Figure:
    """Apply the shared theme, letting callers override individual keys."""
    fig.update_layout({**BASE_LAYOUT, "height": height, **overrides})
    return fig
