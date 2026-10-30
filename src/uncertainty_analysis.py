"""
Uncertainty and Risk Analysis Module for WhatIf AI.

Implements the "Future Scenario Explorer" feature:
- Optimistic, Moderate, and Pessimistic scenario calculations
- All scenarios use actual compound interest calculations (no hardcoded results)
- Configurable assumptions per scenario
- Returns structured scenario data with projected metrics

Mathematical model:
  FV = PV * (1 + r_m)^n  +  PMT * [((1 + r_m)^n - 1) / r_m]
  Real FV = FV / (1 + i)^t

These are HYPOTHETICAL scenario projections, not guaranteed financial outcomes.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import math
import pandas as pd

from src.calculations import (
    SimulationInputs,
    calculate_simulation,
    generate_monthly_schedule,
    format_currency_inr,
)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class UncertaintyScenarioConfig:
    """User-configurable assumptions for each uncertainty scenario."""
    monthly_contribution: float
    annual_inflation: float
    annual_return: float
    duration_years: int
    label: str          # "Optimistic" | "Moderate" | "Pessimistic"
    color: str
    description: str


@dataclass
class UncertaintyScenarioResult:
    """Calculated outcomes for one uncertainty scenario."""
    config: UncertaintyScenarioConfig
    projected_ending_balance: float
    total_contributions: float
    initial_savings: float
    estimated_growth: float
    inflation_adjusted_balance: float
    purchasing_power_loss: float
    real_return_rate: float
    total_months: int


@dataclass
class FutureScenarioExplorerResult:
    """Full result from the Future Scenario Explorer."""
    optimistic: UncertaintyScenarioResult
    moderate: UncertaintyScenarioResult
    pessimistic: UncertaintyScenarioResult
    optimism_pessimism_diff: float    # Optimistic balance - Pessimistic balance
    trajectory_df: pd.DataFrame      # Multi-scenario monthly trajectory for charts


# ---------------------------------------------------------------------------
# Default scenario configurations
# ---------------------------------------------------------------------------

def get_default_scenario_configs(
    base_contribution: float = 8000.0,
    base_inflation: float = 5.0,
    base_return: float = 0.0,
    base_duration: int = 5,
) -> dict:
    """
    Returns default configurations for the three uncertainty scenarios.
    Optimistic: higher return, lower inflation, higher contribution.
    Moderate:   user's current assumptions (base).
    Pessimistic: lower return, higher inflation, lower contribution.
    """
    return {
        "optimistic": UncertaintyScenarioConfig(
            monthly_contribution=round(base_contribution * 1.20, -2),
            annual_inflation=max(0.0, base_inflation - 1.5),
            annual_return=min(20.0, base_return + 3.0) if base_return > 0 else 8.0,
            duration_years=base_duration,
            label="Optimistic",
            color="#10b981",  # Emerald green
            description=(
                "Higher assumed return, lower inflation, and 20% more monthly savings. "
                "Represents a favourable but plausible long-term financial environment."
            ),
        ),
        "moderate": UncertaintyScenarioConfig(
            monthly_contribution=base_contribution,
            annual_inflation=base_inflation,
            annual_return=base_return,
            duration_years=base_duration,
            label="Moderate",
            color="#4f46e5",  # Indigo
            description=(
                "Your current assumptions unchanged. Serves as the central reference scenario."
            ),
        ),
        "pessimistic": UncertaintyScenarioConfig(
            monthly_contribution=max(0.0, round(base_contribution * 0.80, -2)),
            annual_inflation=min(15.0, base_inflation + 2.0),
            annual_return=max(0.0, base_return - 3.0),
            duration_years=base_duration,
            label="Pessimistic",
            color="#f43f5e",  # Rose red
            description=(
                "Lower assumed return, higher inflation, and 20% less monthly savings. "
                "Represents challenging economic headwinds."
            ),
        ),
    }


# ---------------------------------------------------------------------------
# Core calculation function
# ---------------------------------------------------------------------------

def _run_uncertainty_scenario(
    config: UncertaintyScenarioConfig,
    initial_savings: float,
    contribution_timing: str = "end",
) -> UncertaintyScenarioResult:
    """
    Calculates the projected outcomes for a single uncertainty scenario.
    Uses the identical mathematical engine as the main Finance Simulator.
    """
    inputs = SimulationInputs(
        monthly_income=0.0,        # Not required for projection math
        essential_expenses=0.0,
        discretionary_expenses=0.0,
        current_savings=initial_savings,
        monthly_contribution=config.monthly_contribution,
        duration_years=config.duration_years,
        annual_inflation=config.annual_inflation,
        annual_return=config.annual_return,
        contribution_timing=contribution_timing,
    )
    out = calculate_simulation(inputs)

    return UncertaintyScenarioResult(
        config=config,
        projected_ending_balance=out.projected_ending_balance,
        total_contributions=out.total_contributed,
        initial_savings=initial_savings,
        estimated_growth=out.estimated_growth,
        inflation_adjusted_balance=out.inflation_adjusted_balance,
        purchasing_power_loss=out.purchasing_power_loss,
        real_return_rate=out.effective_real_return_rate,
        total_months=out.total_months,
    )


def compute_future_scenario_explorer(
    optimistic_config: UncertaintyScenarioConfig,
    moderate_config: UncertaintyScenarioConfig,
    pessimistic_config: UncertaintyScenarioConfig,
    initial_savings: float = 50000.0,
    contribution_timing: str = "end",
) -> FutureScenarioExplorerResult:
    """
    Computes the Future Scenario Explorer analysis across three scenarios.

    IMPORTANT: These are hypothetical scenario projections based on user-specified
    assumptions. They do not represent guaranteed financial outcomes or forecasts.

    Parameters
    ----------
    optimistic_config : Config for the optimistic scenario
    moderate_config   : Config for the moderate/baseline scenario
    pessimistic_config: Config for the pessimistic scenario
    initial_savings   : Starting savings balance (same for all three scenarios)
    contribution_timing: "end" or "beginning" (annuity convention)

    Returns
    -------
    FutureScenarioExplorerResult with all three calculated outcomes and trajectory data
    """
    opt = _run_uncertainty_scenario(optimistic_config, initial_savings, contribution_timing)
    mod = _run_uncertainty_scenario(moderate_config, initial_savings, contribution_timing)
    pess = _run_uncertainty_scenario(pessimistic_config, initial_savings, contribution_timing)

    # Build monthly trajectory dataframe for charting
    trajectory_records = []
    for scenario_result, label, color in [
        (opt, "Optimistic", optimistic_config.color),
        (mod, "Moderate", moderate_config.color),
        (pess, "Pessimistic", pessimistic_config.color),
    ]:
        inputs = SimulationInputs(
            monthly_income=0.0,
            essential_expenses=0.0,
            discretionary_expenses=0.0,
            current_savings=initial_savings,
            monthly_contribution=scenario_result.config.monthly_contribution,
            duration_years=scenario_result.config.duration_years,
            annual_inflation=scenario_result.config.annual_inflation,
            annual_return=scenario_result.config.annual_return,
            contribution_timing=contribution_timing,
        )
        monthly_df = generate_monthly_schedule(inputs)
        for _, row in monthly_df.iterrows():
            trajectory_records.append({
                "Scenario": label,
                "Color": color,
                "Month": int(row["Month"]),
                "Year": round(row["Month"] / 12.0, 2),
                "Nominal_Balance": row["Closing_Balance"],
                "Real_Balance": row["Real_Balance"],
                "Cumulative_Contributions": row["Cumulative_Contributions"],
                "Cumulative_Growth": row["Cumulative_Growth"],
            })

    trajectory_df = pd.DataFrame(trajectory_records)

    return FutureScenarioExplorerResult(
        optimistic=opt,
        moderate=mod,
        pessimistic=pess,
        optimism_pessimism_diff=(
            opt.projected_ending_balance - pess.projected_ending_balance
        ),
        trajectory_df=trajectory_df,
    )


# ---------------------------------------------------------------------------
# Textual explanation generators
# ---------------------------------------------------------------------------

def explain_scenario_spread(result: FutureScenarioExplorerResult) -> str:
    """
    Generates a plain-English explanation of the spread between optimistic
    and pessimistic outcomes.
    """
    diff = result.optimism_pessimism_diff
    opt_bal = result.optimistic.projected_ending_balance
    pess_bal = result.pessimistic.projected_ending_balance
    mod_bal = result.moderate.projected_ending_balance
    dur = result.moderate.config.duration_years

    return (
        f"Over {dur} years, the difference between the Optimistic scenario "
        f"({format_currency_inr(opt_bal)}) and the Pessimistic scenario "
        f"({format_currency_inr(pess_bal)}) is {format_currency_inr(diff)}. "
        f"The Moderate scenario projects {format_currency_inr(mod_bal)}. "
        f"This spread illustrates the range of plausible outcomes under different "
        f"economic and behavioural assumptions — not a prediction of which will occur."
    )
