"""Shared Plotly styling so every chart uses the same light theme."""

from typing import Any

import plotly.graph_objects as go

NAVY = "#1E3A8A"
BLUE = "#2563EB"
AMBER = "#d97706"
RED = "#dc2626"
GREEN = "#16a34a"
PURPLE = "#7c3aed"
ORANGE = "#ea580c"

SCOPE_COLORS = {1: AMBER, 2: BLUE}
SCOPE_LABEL_COLORS = {"Scope 1": AMBER, "Scope 2": BLUE}

GRID_AXIS = {"gridcolor": "#f1f5f9", "showgrid": True, "zeroline": False}

BASE_LAYOUT: dict[str, Any] = {
    "paper_bgcolor": "#ffffff",
    "plot_bgcolor": "#ffffff",
    "font": {"family": "Inter, sans-serif", "color": "#334155"},
    "margin": {"t": 45, "b": 25, "l": 10, "r": 10},
    "legend": {"bgcolor": "rgba(255,255,255,0.9)", "bordercolor": "#e2e8f0", "borderwidth": 1},
    "xaxis": GRID_AXIS,
    "yaxis": GRID_AXIS,
}


def apply_layout(fig: go.Figure, height: int, **overrides: Any) -> go.Figure:
    """Apply the shared theme, letting callers override individual keys."""
    fig.update_layout({**BASE_LAYOUT, "height": height, **overrides})
    return fig
