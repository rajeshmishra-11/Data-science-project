"""
Unit tests for visualization layout, spacing, and responsive configuration.
Verifies all charts have non-overlapping margins, valid titles, accessible legends,
and consistent SaaS styling.
"""

import pytest
import plotly.graph_objects as go
import pandas as pd
from src.calculations import (
    SimulationInputs,
    calculate_simulation,
    generate_monthly_schedule,
)
from src.scenarios import get_default_preset_scenarios, build_multi_scenario_trajectory_dataframe
from src.sensitivity import compute_tornado_analysis, compute_1d_sweep_contribution
from src.visualizations import (
    plot_wealth_accumulation_trajectory,
    plot_nominal_vs_real_purchasing_power,
    plot_asset_composition_breakdown,
    plot_scenario_comparison_trajectories,
    plot_tornado_sensitivity_chart,
    plot_1d_sweep_curve,
    _apply_saas_theme,
    PLOTLY_CONFIG,
    PALETTE,
)


def test_saas_theme_layout_separation():
    """Verifies that the base styling theme sets safe non-overlapping margins and legend."""
    fig = go.Figure(data=[go.Scatter(x=[1, 2], y=[1, 2], name="Series A")])
    _apply_saas_theme(fig, title="Test Chart Title", subtitle="Test descriptive subtitle")

    layout = fig.layout
    # Margin top must be at least 95px to house title, subtitle, and legend separately
    assert layout.margin.t >= 95
    assert layout.margin.l >= 50

    # Title must be top-anchored and container-referenced
    assert layout.title.yref == "container"
    assert layout.title.y >= 0.95
    assert layout.title.x == 0.0 or layout.title.x == 0.01

    # Legend must be above plot area and separated
    assert layout.legend.orientation == "h"
    assert layout.legend.xanchor == "left"
    assert layout.legend.y >= 1.0


def test_all_chart_generators_produce_valid_figures():
    """Verifies that all 6 chart generators execute cleanly and have valid layout."""
    inputs = SimulationInputs()
    outputs = calculate_simulation(inputs)
    monthly_df = generate_monthly_schedule(inputs)

    # 1. Wealth Trajectory
    fig_traj = plot_wealth_accumulation_trajectory(monthly_df, target_amount=1000000.0)
    assert isinstance(fig_traj, go.Figure)
    assert fig_traj.layout.margin.t >= 100

    # 2. Nominal vs Real Purchasing Power
    fig_real = plot_nominal_vs_real_purchasing_power(monthly_df, annual_inflation=inputs.annual_inflation)
    assert isinstance(fig_real, go.Figure)
    assert fig_real.layout.margin.t >= 100

    # 3. Asset Composition
    fig_comp = plot_asset_composition_breakdown(outputs)
    assert isinstance(fig_comp, go.Figure)
    assert fig_comp.layout.margin.t >= 80

    # 4. Scenario Comparison
    presets = get_default_preset_scenarios(inputs)
    traj_df = build_multi_scenario_trajectory_dataframe(presets)
    colors_map = {s.name: s.color for s in presets}
    fig_scenarios = plot_scenario_comparison_trajectories(traj_df, colors_map)
    assert isinstance(fig_scenarios, go.Figure)
    assert fig_scenarios.layout.margin.t >= 100

    # 5. Tornado Sensitivity
    sens_report = compute_tornado_analysis(inputs)
    fig_tornado = plot_tornado_sensitivity_chart(sens_report)
    assert isinstance(fig_tornado, go.Figure)
    # Tornado needs extra left margin for parameter labels
    assert fig_tornado.layout.margin.l >= 150

    # 6. 1D Sweep Curve
    sweep_df = compute_1d_sweep_contribution(inputs)
    fig_sweep = plot_1d_sweep_curve(sweep_df, "Monthly_Contribution", "Monthly Contribution", "Contribution Sweep")
    assert isinstance(fig_sweep, go.Figure)
    assert fig_sweep.layout.margin.t >= 100


def test_plotly_config_attributes():
    """Verifies that the shared Plotly config is configured for responsive and non-intrusive toolbar."""
    assert PLOTLY_CONFIG["responsive"] is True
    assert PLOTLY_CONFIG["displayModeBar"] == "hover"
    assert PLOTLY_CONFIG["displaylogo"] is False
    assert "lasso2d" in PLOTLY_CONFIG["modeBarButtonsToRemove"]
