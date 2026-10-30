"""
Visualizations Module for WhatIf AI.

Generates responsive, interactive Plotly charts with a bespoke SaaS aesthetic:
- Off-white/clean canvas
- Indigo/Violet accent hierarchy
- Indian Rupee (₹) hover formatting
- Clean gridlines, accessible legends, and custom tooltips
- Zero-overlap layout geometry: strictly separated title, legend, modebar, and axes.
"""

from typing import Dict, List, Optional, Any
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st

from src.calculations import SimulationInputs, SimulationOutputs, format_currency_inr
from src.scenarios import Scenario
from src.sensitivity import SensitivityReport

__all__ = [
    "PALETTE",
    "PLOTLY_CONFIG",
    "render_plotly_chart",
    "plot_wealth_accumulation_trajectory",
    "plot_nominal_vs_real_purchasing_power",
    "plot_asset_composition_breakdown",
    "plot_scenario_comparison_trajectories",
    "plot_tornado_sensitivity_chart",
    "plot_1d_sweep_curve",
    "plot_uncertainty_scenario_trajectories",
    "plot_uncertainty_summary_bars",
    "plot_experiment_response_curve",
    "plot_experiment_grouped_bars",
    "_apply_saas_theme",
]

# Design System Colors
PALETTE = {
    "bg": "rgba(255, 255, 255, 0)",
    "card_bg": "#ffffff",
    "text_primary": "#0f172a",
    "text_secondary": "#64748b",
    "grid": "#f1f5f9",
    "indigo": "#4f46e5",
    "indigo_light": "#818cf8",
    "violet": "#7c3aed",
    "emerald": "#10b981",
    "amber": "#f59e0b",
    "rose": "#f43f5e",
    "cyan": "#06b6d4",
    "border": "#e2e8f0",
}

# Standardized Plotly Configuration for Streamlit
PLOTLY_CONFIG: Dict[str, Any] = {
    "responsive": True,
    "displayModeBar": "hover",  # Shows toolbar only on mouse hover
    "displaylogo": False,
    "modeBarButtonsToRemove": [
        "lasso2d",
        "select2d",
        "autoScale2d",
        "hoverClosestCartesian",
        "hoverCompareCartesian",
        "toggleSpikelines",
    ],
    "toImageButtonOptions": {
        "format": "png",
        "filename": "whatif_ai_chart",
        "height": 720,
        "width": 1280,
        "scale": 2,
    },
}


def render_plotly_chart(fig: go.Figure, key: Optional[str] = None):
    """
    Standardized Streamlit renderer for Plotly figures.
    Guarantees container-width responsiveness and non-intrusive hover toolbar.
    """
    try:
        st.plotly_chart(
            fig,
            width="stretch",
            config=PLOTLY_CONFIG,
            key=key,
        )
    except TypeError:
        st.plotly_chart(
            fig,
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key=key,
        )


def _apply_saas_theme(
    fig: go.Figure,
    title: str = "",
    subtitle: str = "",
    height: int = 440,
    margin_top: int = 110,
    margin_left: int = 70,
    margin_right: int = 30,
    margin_bottom: int = 55,
    show_legend: bool = True,
    legend_orientation: str = "h",
    legend_y: float = 1.02,
    legend_x: float = 0.0,
    legend_yanchor: str = "bottom",
    legend_xanchor: str = "left",
) -> go.Figure:
    """
    Applies unified typography, borders, hover styling, and grid rules.
    Enforces a strict vertical layout budget:
    - Title & Subtitle: top container banner (y=0.98, yanchor='top', yref='container')
    - Legend: positioned cleanly between title and plot area (yanchor='bottom', y=1.02 paper)
    - Modebar: top-right corner, non-overlapping with left-aligned legend and title
    - Axes: automargin=True with distinct standoff
    """
    title_text = f"<b>{title}</b>"
    if subtitle:
        title_text += f"<br><span style='font-size:12px; font-weight:normal; color:{PALETTE['text_secondary']};'>{subtitle}</span>"

    fig.update_layout(
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
            color=PALETTE["text_primary"],
            size=12,
        ),
        paper_bgcolor=PALETTE["bg"],
        plot_bgcolor=PALETTE["bg"],
        height=height,
        autosize=True,
        margin=dict(
            l=margin_left,
            r=margin_right,
            t=margin_top if title else 35,
            b=margin_bottom,
            pad=4,
        ),
        title=dict(
            text=title_text if title else None,
            font=dict(
                size=15,
                color=PALETTE["text_primary"],
                family="Inter, sans-serif",
            ),
            x=0.0,
            xanchor="left",
            y=0.98,
            yanchor="top",
            yref="container",
            pad=dict(b=8, l=0, r=0, t=2),
        ),
        showlegend=show_legend,
        legend=dict(
            orientation=legend_orientation,
            yanchor=legend_yanchor,
            y=legend_y,
            xanchor=legend_xanchor,
            x=legend_x,
            bgcolor="rgba(255, 255, 255, 0.85)",
            bordercolor=PALETTE["border"],
            borderwidth=1,
            font=dict(size=11.5, color=PALETTE["text_primary"]),
            itemsizing="constant",
            tracegroupgap=6,
        ) if show_legend else None,
        hoverlabel=dict(
            bgcolor="#0f172a",
            font_size=12.5,
            font_family="Inter, sans-serif",
            font_color="#ffffff",
            bordercolor="#0f172a",
        ),
        modebar=dict(
            orientation="h",
            bgcolor="rgba(255, 255, 255, 0.85)",
            color="#64748b",
            activecolor="#4f46e5",
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor=PALETTE["grid"],
            gridwidth=1,
            linecolor=PALETTE["border"],
            zeroline=True,
            zerolinecolor=PALETTE["border"],
            tickfont=dict(size=11.5, color=PALETTE["text_secondary"]),
            title_font=dict(size=12.5, color=PALETTE["text_primary"]),
            automargin=True,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=PALETTE["grid"],
            gridwidth=1,
            linecolor=PALETTE["border"],
            zeroline=True,
            zerolinecolor=PALETTE["border"],
            tickfont=dict(size=11.5, color=PALETTE["text_secondary"]),
            title_font=dict(size=12.5, color=PALETTE["text_primary"]),
            automargin=True,
        ),
    )
    return fig


def plot_wealth_accumulation_trajectory(monthly_df: pd.DataFrame, target_amount: Optional[float] = None) -> go.Figure:
    """
    Renders an interactive stacked area / trajectory chart showing:
    - Initial Balance
    - Cumulative Monthly Contributions
    - Compound Growth
    - Optional Savings Target benchmark line
    """
    fig = go.Figure()

    # Time axis in Years
    x_vals = monthly_df["Month"] / 12.0

    # 1. Base principal
    p0 = monthly_df["Opening_Balance"].iloc[0]
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=[p0] * len(monthly_df),
        mode="lines",
        name="Initial Savings",
        line=dict(width=1.5, color="#94a3b8"),
        fill="tozeroy",
        fillcolor="rgba(203, 213, 225, 0.35)",
        hovertemplate="Initial Savings: ₹%{y:,.0f}<extra></extra>",
    ))

    # 2. Cumulative Principal (Initial + Contributions)
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=monthly_df["Cumulative_Principal"],
        mode="lines",
        name="Total Contributed",
        line=dict(width=2, color=PALETTE["indigo"]),
        fill="tonexty",
        fillcolor="rgba(79, 70, 229, 0.20)",
        hovertemplate="Total Principal: ₹%{y:,.0f}<br>Year %{x:.1f}<extra></extra>",
    ))

    # 3. Total Closing Balance (including compound growth)
    has_growth = monthly_df["Cumulative_Growth"].iloc[-1] > 10.0
    if has_growth:
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=monthly_df["Closing_Balance"],
            mode="lines",
            name="Ending Balance (with Growth)",
            line=dict(width=2.5, color=PALETTE["emerald"]),
            fill="tonexty",
            fillcolor="rgba(16, 185, 129, 0.20)",
            hovertemplate="Total Projected: ₹%{y:,.0f}<br>Growth: ₹%{customdata:,.0f}<br>Year %{x:.1f}<extra></extra>",
            customdata=monthly_df["Cumulative_Growth"],
        ))

    # 4. Optional Target Benchmark line
    if target_amount and target_amount > 0:
        fig.add_trace(go.Scatter(
            x=[0, x_vals.iloc[-1]],
            y=[target_amount, target_amount],
            mode="lines",
            name="Target Goal",
            line=dict(color=PALETTE["rose"], width=2, dash="dash"),
            hovertemplate="Target Goal: ₹%{y:,.0f}<extra></extra>",
        ))

    fig.update_xaxes(title_text="Timeline (Years)", ticksuffix=" yr")
    fig.update_yaxes(title_text="Value in INR (₹)", tickprefix="₹", tickformat=",.0f")
    _apply_saas_theme(
        fig,
        title="Projected Wealth Accumulation Trajectory",
        subtitle="Breakdown of initial savings, cumulative monthly deposits, and compound growth.",
        height=440,
        margin_top=115,
        margin_left=75,
    )
    return fig


def plot_nominal_vs_real_purchasing_power(monthly_df: pd.DataFrame, annual_inflation: float) -> go.Figure:
    """
    Visualizes the impact of inflation on future savings purchasing power.
    Shows Nominal Balance vs Real (Inflation-Adjusted) Balance with zero text overlap.
    """
    fig = go.Figure()
    x_vals = monthly_df["Month"] / 12.0

    # Nominal Balance
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=monthly_df["Closing_Balance"],
        mode="lines",
        name="Nominal Balance",
        line=dict(width=2.5, color=PALETTE["indigo"]),
        hovertemplate="Nominal Balance: ₹%{y:,.0f}<br>Year %{x:.1f}<extra></extra>",
    ))

    # Real Purchasing Power
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=monthly_df["Real_Balance"],
        mode="lines",
        name=f"Real Value ({annual_inflation:.1f}% Inflation)",
        line=dict(width=2.5, color=PALETTE["amber"], dash="solid"),
        hovertemplate="Real Value: ₹%{y:,.0f}<br>Year %{x:.1f}<extra></extra>",
    ))

    # Area gap representing purchasing power erosion
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=monthly_df["Closing_Balance"],
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=x_vals,
        y=monthly_df["Real_Balance"],
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(245, 158, 11, 0.14)",
        name="Inflation Erosion Gap",
        hoverinfo="skip",
    ))

    fig.update_xaxes(title_text="Timeline (Years)", ticksuffix=" yr")
    fig.update_yaxes(title_text="Value in INR (₹)", tickprefix="₹", tickformat=",.0f")
    _apply_saas_theme(
        fig,
        title="Nominal Balance vs. Inflation-Adjusted Real Value",
        subtitle=f"Visualizing inflation purchasing power drag assuming {annual_inflation:.1f}% annual inflation.",
        height=440,
        margin_top=115,
        margin_left=75,
    )
    return fig


def plot_asset_composition_breakdown(outputs: SimulationOutputs) -> go.Figure:
    """
    Donut chart displaying the structural composition of the ending corpus:
    - Initial Savings
    - Total Monthly Contributions
    - Compound Interest / Growth
    Uses clean interior percentages and separated legend to prevent label collisions.
    """
    labels = ["Initial Savings", "Total Contributions", "Estimated Compound Growth"]
    values = [
        max(0.0, outputs.inputs.current_savings),
        max(0.0, outputs.total_contributed),
        max(0.0, outputs.estimated_growth),
    ]
    colors = ["#94a3b8", PALETTE["indigo"], PALETTE["emerald"]]

    fig = go.Figure(data=[
        go.Pie(
            labels=labels,
            values=values,
            hole=0.62,
            marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
            textinfo="percent",
            textposition="inside",
            insidetextorientation="horizontal",
            hovertemplate="<b>%{label}</b><br>Amount: ₹%{value:,.0f}<br>Share: %{percent}<extra></extra>",
        )
    ])

    fig.update_layout(
        annotations=[
            dict(
                text=f"Total Corpus<br><b>{format_currency_inr(outputs.projected_ending_balance)}</b>",
                x=0.5, y=0.5,
                font_size=15,
                font_family="Inter, sans-serif",
                showarrow=False,
            )
        ]
    )

    _apply_saas_theme(
        fig,
        title="Final Corpus Composition Breakdown",
        subtitle="Proportional distribution of initial capital, contributions, and compound earnings.",
        height=430,
        margin_top=95,
        margin_left=40,
        margin_right=40,
    )
    return fig


def plot_scenario_comparison_trajectories(multi_scenario_df: pd.DataFrame, scenario_colors: dict) -> go.Figure:
    """
    Plots multi-line trajectories for comparing 3+ scenarios on a single canvas.
    Accommodates multiple series names without title collision.
    """
    fig = go.Figure()

    scenarios = multi_scenario_df["Scenario"].unique()
    for scn in scenarios:
        sub = multi_scenario_df[multi_scenario_df["Scenario"] == scn]
        color = scenario_colors.get(scn, PALETTE["indigo"])

        fig.add_trace(go.Scatter(
            x=sub["Year"],
            y=sub["Nominal_Balance"],
            mode="lines+markers",
            name=scn,
            line=dict(width=2.5, color=color),
            marker=dict(size=4),
            hovertemplate=f"<b>{scn}</b><br>Balance: ₹%{{y:,.0f}}<br>Year: %{{x:.1f}}<extra></extra>",
        ))

    fig.update_xaxes(title_text="Timeline (Years)", ticksuffix=" yr")
    fig.update_yaxes(title_text="Projected Balance (₹)", tickprefix="₹", tickformat=",.0f")
    _apply_saas_theme(
        fig,
        title="Multi-Scenario Wealth Trajectory Comparison",
        subtitle="Comparing projected accumulation pathways across scenarios over time.",
        height=460,
        margin_top=120,
        margin_left=75,
    )
    return fig


def plot_tornado_sensitivity_chart(sensitivity_report: SensitivityReport) -> go.Figure:
    """
    Renders a Tornado sensitivity chart displaying parameter impact swings on ending balance.
    Sorted descending by impact swing.
    Allocates generous left margin (185px) to eliminate parameter label clipping.
    """
    results = sensitivity_report.ranked_by_impact
    y_labels = [r.display_name for r in results]
    base_val = sensitivity_report.base_outcome

    # For horizontal bar ranges:
    low_diffs = [r.low_outcome - base_val for r in results]
    high_diffs = [r.high_outcome - base_val for r in results]

    fig = go.Figure()

    # Low swing (downside or left impact)
    fig.add_trace(go.Bar(
        y=y_labels,
        x=low_diffs,
        base=0,
        orientation="h",
        name="Low Bound Tested",
        marker=dict(color="#f43f5e", line=dict(color="#e11d48", width=1)),
        hovertemplate="<b>%{y} (Low Bound)</b><br>Delta from Base: ₹%{x:,.0f}<br>Outcome: ₹%{customdata:,.0f}<extra></extra>",
        customdata=[r.low_outcome for r in results],
    ))

    # High swing (upside or right impact)
    fig.add_trace(go.Bar(
        y=y_labels,
        x=high_diffs,
        base=0,
        orientation="h",
        name="High Bound Tested",
        marker=dict(color="#10b981", line=dict(color="#059669", width=1)),
        hovertemplate="<b>%{y} (High Bound)</b><br>Delta from Base: ₹%{x:,.0f}<br>Outcome: ₹%{customdata:,.0f}<extra></extra>",
        customdata=[r.high_outcome for r in results],
    ))

    fig.update_xaxes(
        title_text="Swing in Projected Balance from Baseline (₹)",
        tickprefix="₹",
        tickformat=",.0f",
        zeroline=True,
        zerolinecolor="#0f172a",
        zerolinewidth=2,
    )
    fig.update_yaxes(title_text="", autorange="reversed", tickfont=dict(size=12))

    _apply_saas_theme(
        fig,
        title="Tornado Sensitivity Analysis (Impact on Final Balance)",
        subtitle=f"Baseline Ending Balance: {format_currency_inr(base_val)}. Bars show balance swings when perturbing parameters independently.",
        height=470,
        margin_top=115,
        margin_left=185,  # Ample space for multi-word parameter labels
        margin_right=35,
    )
    return fig


def plot_1d_sweep_curve(sweep_df: pd.DataFrame, x_col: str, x_label: str, title: str) -> go.Figure:
    """
    Renders a continuous response curve showing ending balance and real purchasing power.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=sweep_df[x_col],
        y=sweep_df["Ending_Balance"],
        mode="lines+markers",
        name="Nominal Ending Balance",
        line=dict(color=PALETTE["indigo"], width=2.5),
        marker=dict(size=5),
        hovertemplate=f"{x_label}: %{{x}}<br>Ending Balance: ₹%{{y:,.0f}}<extra></extra>",
    ))

    if "Real_Value" in sweep_df.columns:
        fig.add_trace(go.Scatter(
            x=sweep_df[x_col],
            y=sweep_df["Real_Value"],
            mode="lines",
            name="Real Purchasing Power",
            line=dict(color=PALETTE["amber"], width=2, dash="dash"),
            hovertemplate=f"{x_label}: %{{x}}<br>Real Value: ₹%{{y:,.0f}}<extra></extra>",
        ))

    fig.update_xaxes(title_text=x_label)
    fig.update_yaxes(title_text="Projected Outcome (₹)", tickprefix="₹", tickformat=",.0f")
    _apply_saas_theme(
        fig,
        title=title,
        subtitle="Continuous functional response curve mapping output variance as input parameter changes.",
        height=440,
        margin_top=115,
        margin_left=75,
    )
    return fig


# ---------------------------------------------------------------------------
# NEW: Uncertainty Analysis Visualizations
# ---------------------------------------------------------------------------

def plot_uncertainty_scenario_trajectories(trajectory_df: pd.DataFrame) -> go.Figure:
    """
    Plots three uncertainty scenario trajectories (Optimistic, Moderate, Pessimistic)
    with a shaded band between optimistic and pessimistic outcomes.
    """
    fig = go.Figure()

    scenario_order = ["Optimistic", "Moderate", "Pessimistic"]
    color_map = {
        "Optimistic": PALETTE["emerald"],
        "Moderate": PALETTE["indigo"],
        "Pessimistic": PALETTE["rose"],
    }
    dash_map = {
        "Optimistic": "solid",
        "Moderate": "solid",
        "Pessimistic": "dash",
    }

    opt_df = trajectory_df[trajectory_df["Scenario"] == "Optimistic"]
    pess_df = trajectory_df[trajectory_df["Scenario"] == "Pessimistic"]

    # Shaded uncertainty band between optimistic and pessimistic
    if not opt_df.empty and not pess_df.empty:
        fig.add_trace(go.Scatter(
            x=opt_df["Year"],
            y=opt_df["Nominal_Balance"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=pess_df["Year"],
            y=pess_df["Nominal_Balance"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(99, 102, 241, 0.08)",
            name="Uncertainty Range",
            hoverinfo="skip",
        ))

    for scenario_name in scenario_order:
        sub = trajectory_df[trajectory_df["Scenario"] == scenario_name]
        if sub.empty:
            continue
        color = color_map.get(scenario_name, PALETTE["indigo"])
        dash = dash_map.get(scenario_name, "solid")
        width = 2.0 if scenario_name == "Moderate" else 2.5

        fig.add_trace(go.Scatter(
            x=sub["Year"],
            y=sub["Nominal_Balance"],
            mode="lines",
            name=scenario_name,
            line=dict(width=width, color=color, dash=dash),
            hovertemplate=(
                f"<b>{scenario_name}</b><br>"
                "Balance: ₹%{y:,.0f}<br>"
                "Year: %{x:.1f}<extra></extra>"
            ),
        ))

    fig.update_xaxes(title_text="Timeline (Years)", ticksuffix=" yr")
    fig.update_yaxes(
        title_text="Projected Balance (₹)",
        tickprefix="₹",
        tickformat=",.0f",
    )
    _apply_saas_theme(
        fig,
        title="Future Scenario Explorer — Three-Scenario Trajectory",
        subtitle=(
            "Optimistic, Moderate, and Pessimistic projections with shaded uncertainty band. "
            "These are hypothetical scenarios, not guaranteed financial outcomes."
        ),
        height=480,
        margin_top=125,
        margin_left=80,
    )
    return fig


def plot_uncertainty_summary_bars(results: dict) -> go.Figure:
    """
    Bar chart comparing the final outcome metrics across three uncertainty scenarios.
    results: dict with keys 'optimistic', 'moderate', 'pessimistic', each a UncertaintyScenarioResult.
    """
    from src.uncertainty_analysis import UncertaintyScenarioResult
    scenario_labels = ["Pessimistic", "Moderate", "Optimistic"]
    scenario_keys = ["pessimistic", "moderate", "optimistic"]
    colors = [PALETTE["rose"], PALETTE["indigo"], PALETTE["emerald"]]

    nominal_vals = [results[k].projected_ending_balance for k in scenario_keys]
    real_vals = [results[k].inflation_adjusted_balance for k in scenario_keys]
    contrib_vals = [results[k].total_contributions for k in scenario_keys]
    growth_vals = [results[k].estimated_growth for k in scenario_keys]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Total Contributions",
        x=scenario_labels,
        y=contrib_vals,
        marker_color=["rgba(244,63,94,0.6)", "rgba(79,70,229,0.6)", "rgba(16,185,129,0.6)"],
        hovertemplate="%{x}<br>Contributions: ₹%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Estimated Growth",
        x=scenario_labels,
        y=[max(0.0, g) for g in growth_vals],
        marker_color=[PALETTE["rose"], PALETTE["indigo"], PALETTE["emerald"]],
        hovertemplate="%{x}<br>Growth: ₹%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        name="Real Purchasing Power",
        x=scenario_labels,
        y=real_vals,
        mode="markers",
        marker=dict(size=14, symbol="diamond", color="#f59e0b", line=dict(width=2, color="#b45309")),
        hovertemplate="%{x}<br>Real Value: ₹%{y:,.0f}<extra></extra>",
    ))

    fig.update_layout(barmode="stack")
    fig.update_xaxes(title_text="Scenario")
    fig.update_yaxes(title_text="Amount (₹)", tickprefix="₹", tickformat=",.0f")
    _apply_saas_theme(
        fig,
        title="Scenario Outcome Comparison — Key Metrics",
        subtitle="Stacked bars show contributions + growth. Diamond markers show inflation-adjusted real value.",
        height=440,
        margin_top=115,
        margin_left=80,
    )
    return fig


# ---------------------------------------------------------------------------
# NEW: Experiment Lab Visualizations
# ---------------------------------------------------------------------------

def plot_experiment_response_curve(
    exp_df: pd.DataFrame,
    x_col: str,
    x_label: str,
    title: str,
    y_col_nominal: str = "Projected_Ending_Balance",
    y_col_real: str = "Real_Purchasing_Power",
    show_real: bool = True,
    subtitle: str = "",
) -> go.Figure:
    """
    Renders a continuous response curve for experiment results.
    Shows both nominal outcome and (optionally) real purchasing power.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=exp_df[x_col],
        y=exp_df[y_col_nominal],
        mode="lines+markers",
        name="Nominal Ending Balance",
        line=dict(color=PALETTE["indigo"], width=2.5),
        marker=dict(size=8, color=PALETTE["indigo"]),
        hovertemplate=f"{x_label}: %{{x}}<br>Nominal Balance: ₹%{{y:,.0f}}<extra></extra>",
    ))

    if show_real and y_col_real in exp_df.columns:
        fig.add_trace(go.Scatter(
            x=exp_df[x_col],
            y=exp_df[y_col_real],
            mode="lines+markers",
            name="Real Purchasing Power",
            line=dict(color=PALETTE["amber"], width=2, dash="dash"),
            marker=dict(size=6, color=PALETTE["amber"]),
            hovertemplate=f"{x_label}: %{{x}}<br>Real Value: ₹%{{y:,.0f}}<extra></extra>",
        ))

    # Highlight the range with a subtle fill
    if len(exp_df) > 1:
        fig.add_trace(go.Scatter(
            x=exp_df[x_col],
            y=exp_df[y_col_nominal],
            mode="lines",
            line=dict(width=0),
            fill="tozeroy",
            fillcolor="rgba(79, 70, 229, 0.05)",
            showlegend=False,
            hoverinfo="skip",
        ))

    fig.update_xaxes(title_text=x_label)
    fig.update_yaxes(title_text="Projected Outcome (₹)", tickprefix="₹", tickformat=",.0f")
    _apply_saas_theme(
        fig,
        title=title,
        subtitle=subtitle or "One-factor-at-a-time (OFAT) experiment holding all other parameters constant.",
        height=440,
        margin_top=115,
        margin_left=80,
    )
    return fig


def plot_experiment_grouped_bars(
    exp_df: pd.DataFrame,
    x_col: str,
    x_label: str,
    title: str,
    subtitle: str = "",
) -> go.Figure:
    """
    Grouped bar chart showing contributions, growth, and real value for each IV level.
    """
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Total Contributions",
        x=exp_df[x_col],
        y=exp_df["Total_Contributions"],
        marker_color="rgba(79, 70, 229, 0.7)",
        hovertemplate=f"{x_label}: %{{x}}<br>Contributions: ₹%{{y:,.0f}}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name="Estimated Growth",
        x=exp_df[x_col],
        y=exp_df["Estimated_Growth"].clip(lower=0),
        marker_color="rgba(16, 185, 129, 0.7)",
        hovertemplate=f"{x_label}: %{{x}}<br>Growth: ₹%{{y:,.0f}}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        name="Real Purchasing Power",
        x=exp_df[x_col],
        y=exp_df["Real_Purchasing_Power"],
        mode="markers",
        marker=dict(size=10, symbol="diamond", color="#f59e0b", line=dict(width=2, color="#b45309")),
        hovertemplate=f"{x_label}: %{{x}}<br>Real Value: ₹%{{y:,.0f}}<extra></extra>",
    ))

    fig.update_layout(barmode="stack")
    fig.update_xaxes(title_text=x_label)
    fig.update_yaxes(title_text="Amount (₹)", tickprefix="₹", tickformat=",.0f")
    _apply_saas_theme(
        fig,
        title=title,
        subtitle=subtitle or "Stacked bars show principal + growth composition. Diamonds show inflation-adjusted real value.",
        height=440,
        margin_top=115,
        margin_left=80,
    )
    return fig
