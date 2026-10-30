"""
Data Science Experiment Lab Module for WhatIf AI.

Project title:
    "Impact of Financial Variables on Long-Term Savings:
     A Scenario-Based Sensitivity Analysis"

Implements four structured experiments:
  A. Monthly Savings Contribution Experiment
  B. Annual Inflation Impact Experiment
  C. Annual Investment Return Experiment
  D. Time Horizon (Duration) Experiment

Experimental design:
  - Each experiment varies one independent variable (IV)
  - All other parameters are held constant (ceteris paribus)
  - Dependent variable (DV): Projected Ending Balance and Real Purchasing Power
  - No statistical inference or significance testing is performed
  - Results are mathematical simulations, not real-world forecasts

All calculations use the same financial engine as the Finance Simulator.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
import pandas as pd
import io

from src.calculations import (
    SimulationInputs,
    calculate_simulation,
    format_currency_inr,
)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class ExperimentDataPoint:
    """A single data point in an experiment."""
    iv_label: str          # Independent variable label
    iv_value: float        # Independent variable value
    ending_balance: float  # Projected nominal ending balance (DV)
    real_value: float      # Inflation-adjusted purchasing power (DV)
    total_contributions: float
    estimated_growth: float


@dataclass
class ExperimentResult:
    """Full result of one experiment."""
    experiment_id: str           # "A" | "B" | "C" | "D"
    title: str
    independent_variable: str
    dependent_variable: str
    fixed_parameters: Dict[str, Any]  # Parameters held constant
    data_points: List[ExperimentDataPoint]
    interpretation: str          # Plain-English explanation
    min_outcome: float
    max_outcome: float
    outcome_range: float         # max - min (spread)
    data_frame: pd.DataFrame     # Structured for charting/export


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _run_experiment_point(
    base_inputs: SimulationInputs,
    override: Dict[str, Any],
) -> ExperimentDataPoint:
    """
    Runs one simulation point with specific parameter override.
    Returns an ExperimentDataPoint.
    """
    iv_label = override.get("iv_label", "")
    iv_value = override.get("iv_value", 0.0)

    inputs = SimulationInputs(
        monthly_income=base_inputs.monthly_income,
        essential_expenses=base_inputs.essential_expenses,
        discretionary_expenses=base_inputs.discretionary_expenses,
        current_savings=base_inputs.current_savings,
        monthly_contribution=override.get("monthly_contribution", base_inputs.monthly_contribution),
        duration_years=int(override.get("duration_years", base_inputs.duration_years)),
        annual_inflation=override.get("annual_inflation", base_inputs.annual_inflation),
        annual_return=override.get("annual_return", base_inputs.annual_return),
        contribution_timing=base_inputs.contribution_timing,
    )
    out = calculate_simulation(inputs)
    return ExperimentDataPoint(
        iv_label=iv_label,
        iv_value=iv_value,
        ending_balance=out.projected_ending_balance,
        real_value=out.inflation_adjusted_balance,
        total_contributions=out.total_contributed,
        estimated_growth=out.estimated_growth,
    )


def _build_experiment_df(data_points: List[ExperimentDataPoint], iv_col: str) -> pd.DataFrame:
    rows = []
    for dp in data_points:
        rows.append({
            iv_col: dp.iv_value,
            "IV_Label": dp.iv_label,
            "Projected_Ending_Balance": dp.ending_balance,
            "Real_Purchasing_Power": dp.real_value,
            "Total_Contributions": dp.total_contributions,
            "Estimated_Growth": dp.estimated_growth,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Experiment A: Monthly Savings Contribution
# ---------------------------------------------------------------------------

def run_experiment_a(
    base_inputs: SimulationInputs,
    contribution_values: List[float] = None,
) -> ExperimentResult:
    """
    Experiment A — Monthly Savings Contribution Experiment.

    Independent Variable: Monthly savings contribution (₹/month)
    Dependent Variable:   Projected ending balance after N years
    Fixed: inflation rate, assumed return, duration, initial savings
    """
    if contribution_values is None:
        # Generate 7 comparison points from ₹1,000 to ₹25,000
        contribution_values = [1000, 3000, 5000, 8000, 12000, 18000, 25000]

    data_points = []
    for c in contribution_values:
        dp = _run_experiment_point(
            base_inputs=base_inputs,
            override={
                "iv_label": f"₹{c:,.0f}/mo",
                "iv_value": float(c),
                "monthly_contribution": float(c),
            },
        )
        data_points.append(dp)

    min_val = min(dp.ending_balance for dp in data_points)
    max_val = max(dp.ending_balance for dp in data_points)
    spread = max_val - min_val

    interpretation = (
        f"As monthly contributions increase from {format_currency_inr(contribution_values[0])}/mo "
        f"to {format_currency_inr(contribution_values[-1])}/mo (holding other parameters constant), "
        f"the projected ending balance increases from {format_currency_inr(min_val)} to "
        f"{format_currency_inr(max_val)} — a spread of {format_currency_inr(spread)}. "
        f"This relationship is linear when the return rate is 0%, and becomes super-linear "
        f"when returns compound on a larger contribution base. "
        f"Current fixed assumptions: {base_inputs.duration_years} years, "
        f"{base_inputs.annual_return:.1f}% return, {base_inputs.annual_inflation:.1f}% inflation."
    )

    return ExperimentResult(
        experiment_id="A",
        title="Experiment A: Impact of Monthly Savings Contribution on Long-Term Balance",
        independent_variable="Monthly Savings Contribution (₹/month)",
        dependent_variable="Projected Ending Balance (₹)",
        fixed_parameters={
            "Annual Return": f"{base_inputs.annual_return:.1f}%",
            "Annual Inflation": f"{base_inputs.annual_inflation:.1f}%",
            "Duration": f"{base_inputs.duration_years} years",
            "Initial Savings": format_currency_inr(base_inputs.current_savings),
        },
        data_points=data_points,
        interpretation=interpretation,
        min_outcome=min_val,
        max_outcome=max_val,
        outcome_range=spread,
        data_frame=_build_experiment_df(data_points, "Monthly_Contribution"),
    )


# ---------------------------------------------------------------------------
# Experiment B: Annual Inflation Impact
# ---------------------------------------------------------------------------

def run_experiment_b(
    base_inputs: SimulationInputs,
    inflation_values: List[float] = None,
) -> ExperimentResult:
    """
    Experiment B — Annual Inflation Impact Experiment.

    Independent Variable: Annual inflation rate (%)
    Dependent Variable:   Real (inflation-adjusted) purchasing power
    Fixed: monthly contribution, assumed return, duration, initial savings
    """
    if inflation_values is None:
        inflation_values = [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0]

    data_points = []
    for inf in inflation_values:
        dp = _run_experiment_point(
            base_inputs=base_inputs,
            override={
                "iv_label": f"{inf:.1f}%",
                "iv_value": float(inf),
                "annual_inflation": float(inf),
            },
        )
        data_points.append(dp)

    # For inflation, DV is Real Purchasing Power
    min_val = min(dp.real_value for dp in data_points)
    max_val = max(dp.real_value for dp in data_points)
    spread = max_val - min_val

    interpretation = (
        f"As annual inflation increases from {inflation_values[0]:.1f}% to "
        f"{inflation_values[-1]:.1f}% (holding other parameters constant), "
        f"the real purchasing power of the final corpus falls from "
        f"{format_currency_inr(max_val)} to {format_currency_inr(min_val)} — "
        f"a reduction of {format_currency_inr(spread)} in today's money. "
        f"Note: The nominal ending balance remains unchanged across these experiments "
        f"because inflation does not affect the accumulation calculation — only the "
        f"real value discount. "
        f"Fixed: {format_currency_inr(base_inputs.monthly_contribution)}/mo contribution, "
        f"{base_inputs.annual_return:.1f}% return, {base_inputs.duration_years} years."
    )

    return ExperimentResult(
        experiment_id="B",
        title="Experiment B: Impact of Annual Inflation on Real Purchasing Power",
        independent_variable="Annual Inflation Rate (%)",
        dependent_variable="Real (Inflation-Adjusted) Purchasing Power (₹)",
        fixed_parameters={
            "Monthly Contribution": format_currency_inr(base_inputs.monthly_contribution),
            "Annual Return": f"{base_inputs.annual_return:.1f}%",
            "Duration": f"{base_inputs.duration_years} years",
            "Initial Savings": format_currency_inr(base_inputs.current_savings),
        },
        data_points=data_points,
        interpretation=interpretation,
        min_outcome=min_val,
        max_outcome=max_val,
        outcome_range=spread,
        data_frame=_build_experiment_df(data_points, "Annual_Inflation"),
    )


# ---------------------------------------------------------------------------
# Experiment C: Annual Investment Return
# ---------------------------------------------------------------------------

def run_experiment_c(
    base_inputs: SimulationInputs,
    return_values: List[float] = None,
) -> ExperimentResult:
    """
    Experiment C — Annual Investment Return Experiment.

    Independent Variable: Assumed annual investment return rate (%)
    Dependent Variable:   Projected nominal ending balance
    Fixed: monthly contribution, inflation, duration, initial savings

    IMPORTANT DISCLAIMER (embedded in interpretation): Higher assumed returns
    represent optimistic scenarios, not guaranteed outcomes. This is a
    mathematical simulation, not financial advice.
    """
    if return_values is None:
        return_values = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 15.0]

    data_points = []
    for ret in return_values:
        dp = _run_experiment_point(
            base_inputs=base_inputs,
            override={
                "iv_label": f"{ret:.1f}%",
                "iv_value": float(ret),
                "annual_return": float(ret),
            },
        )
        data_points.append(dp)

    min_val = min(dp.ending_balance for dp in data_points)
    max_val = max(dp.ending_balance for dp in data_points)
    spread = max_val - min_val

    interpretation = (
        f"As the assumed annual return increases from {return_values[0]:.1f}% to "
        f"{return_values[-1]:.1f}% (holding other parameters constant), "
        f"the projected ending balance increases from {format_currency_inr(min_val)} "
        f"to {format_currency_inr(max_val)} — a spread of {format_currency_inr(spread)}. "
        f"At 0% return, the balance is purely principal. At higher rates, compound growth "
        f"accelerates exponentially over time. "
        f"IMPORTANT: These return rates are user-specified assumptions used for simulation "
        f"purposes. They do not constitute guaranteed investment outcomes or financial advice. "
        f"Actual investment returns are subject to market risk, volatility, and economic conditions. "
        f"Fixed: {format_currency_inr(base_inputs.monthly_contribution)}/mo, "
        f"{base_inputs.annual_inflation:.1f}% inflation, {base_inputs.duration_years} years."
    )

    return ExperimentResult(
        experiment_id="C",
        title="Experiment C: Impact of Assumed Return Rate on Projected Ending Balance",
        independent_variable="Assumed Annual Return Rate (%)",
        dependent_variable="Projected Nominal Ending Balance (₹)",
        fixed_parameters={
            "Monthly Contribution": format_currency_inr(base_inputs.monthly_contribution),
            "Annual Inflation": f"{base_inputs.annual_inflation:.1f}%",
            "Duration": f"{base_inputs.duration_years} years",
            "Initial Savings": format_currency_inr(base_inputs.current_savings),
        },
        data_points=data_points,
        interpretation=interpretation,
        min_outcome=min_val,
        max_outcome=max_val,
        outcome_range=spread,
        data_frame=_build_experiment_df(data_points, "Annual_Return"),
    )


# ---------------------------------------------------------------------------
# Experiment D: Time Horizon
# ---------------------------------------------------------------------------

def run_experiment_d(
    base_inputs: SimulationInputs,
    duration_values: List[int] = None,
) -> ExperimentResult:
    """
    Experiment D — Time Horizon Experiment.

    Independent Variable: Simulation duration (years)
    Dependent Variable:   Projected ending balance
    Fixed: monthly contribution, inflation, assumed return, initial savings
    """
    if duration_values is None:
        duration_values = [1, 2, 3, 5, 7, 10, 15, 20, 25, 30]

    data_points = []
    for dur in duration_values:
        dp = _run_experiment_point(
            base_inputs=base_inputs,
            override={
                "iv_label": f"{dur}yr",
                "iv_value": float(dur),
                "duration_years": int(dur),
            },
        )
        data_points.append(dp)

    min_val = min(dp.ending_balance for dp in data_points)
    max_val = max(dp.ending_balance for dp in data_points)
    spread = max_val - min_val

    interpretation = (
        f"As the time horizon extends from {duration_values[0]} to {duration_values[-1]} years, "
        f"the projected ending balance grows from {format_currency_inr(min_val)} to "
        f"{format_currency_inr(max_val)} — a spread of {format_currency_inr(spread)}. "
        f"With a non-zero assumed return of {base_inputs.annual_return:.1f}%, "
        + (
            "compound growth accelerates non-linearly as duration extends, "
            "demonstrating the exponential power of compounding over time. "
            if base_inputs.annual_return > 0 else
            "the growth is linear since all accumulation is from direct contributions (0% return). "
        )
        + f"Fixed: {format_currency_inr(base_inputs.monthly_contribution)}/mo contribution, "
        f"{base_inputs.annual_return:.1f}% return, {base_inputs.annual_inflation:.1f}% inflation."
    )

    return ExperimentResult(
        experiment_id="D",
        title="Experiment D: Impact of Time Horizon on Long-Term Wealth Accumulation",
        independent_variable="Simulation Duration (Years)",
        dependent_variable="Projected Nominal Ending Balance (₹)",
        fixed_parameters={
            "Monthly Contribution": format_currency_inr(base_inputs.monthly_contribution),
            "Annual Return": f"{base_inputs.annual_return:.1f}%",
            "Annual Inflation": f"{base_inputs.annual_inflation:.1f}%",
            "Initial Savings": format_currency_inr(base_inputs.current_savings),
        },
        data_points=data_points,
        interpretation=interpretation,
        min_outcome=min_val,
        max_outcome=max_val,
        outcome_range=spread,
        data_frame=_build_experiment_df(data_points, "Duration_Years"),
    )


# ---------------------------------------------------------------------------
# CSV Export helpers
# ---------------------------------------------------------------------------

def export_experiment_results_csv(
    exp_a: ExperimentResult,
    exp_b: ExperimentResult,
    exp_c: ExperimentResult,
    exp_d: ExperimentResult,
) -> str:
    """
    Generates a combined CSV file with all four experiment result tables,
    separated by headers.
    """
    output = io.StringIO()

    for exp in [exp_a, exp_b, exp_c, exp_d]:
        output.write(f"# {exp.title}\n")
        output.write(f"# Independent Variable: {exp.independent_variable}\n")
        output.write(f"# Dependent Variable: {exp.dependent_variable}\n")
        for k, v in exp.fixed_parameters.items():
            output.write(f"# Fixed - {k}: {v}\n")
        output.write("#\n")
        exp.data_frame.to_csv(output, index=False)
        output.write("\n")

    return output.getvalue()


def export_experiment_summary_report(
    exp_a: ExperimentResult,
    exp_b: ExperimentResult,
    exp_c: ExperimentResult,
    exp_d: ExperimentResult,
    base_inputs: SimulationInputs,
) -> str:
    """
    Generates a structured plain-text experiment summary report.
    Suitable for academic submission documentation.
    """
    lines = []
    lines.append("=" * 70)
    lines.append("WHATIF AI — DATA SCIENCE EXPERIMENT LAB SUMMARY REPORT")
    lines.append("Impact of Financial Variables on Long-Term Savings:")
    lines.append("A Scenario-Based Sensitivity Analysis")
    lines.append("=" * 70)
    lines.append("")
    lines.append("METHODOLOGY")
    lines.append("-" * 40)
    lines.append("Experimental Design: Controlled one-factor-at-a-time (OFAT) simulation.")
    lines.append("Each experiment varies one independent variable (IV) while all")
    lines.append("other parameters are held constant (ceteris paribus).")
    lines.append("")
    lines.append("Mathematical Model (Monthly Compounding Ordinary Annuity):")
    lines.append("  FV = PV * (1 + r_m)^n + PMT * [((1 + r_m)^n - 1) / r_m]")
    lines.append("  Where r_m = annual_return / (100 * 12), n = duration * 12")
    lines.append("  Real FV = FV / (1 + i)^t  [Fisher deflation formula]")
    lines.append("")
    lines.append("IMPORTANT LIMITATIONS:")
    lines.append("  - Results are mathematical simulations, not financial forecasts.")
    lines.append("  - No statistical significance tests were performed.")
    lines.append("  - Real-world outcomes depend on market conditions and individual behavior.")
    lines.append("  - Return assumptions are hypothetical and NOT guaranteed.")
    lines.append("")
    lines.append("BASE SIMULATION PARAMETERS")
    lines.append("-" * 40)
    lines.append(f"  Monthly Income:     {format_currency_inr(base_inputs.monthly_income)}")
    lines.append(f"  Initial Savings:    {format_currency_inr(base_inputs.current_savings)}")
    lines.append(f"  Monthly Contrib.:   {format_currency_inr(base_inputs.monthly_contribution)}")
    lines.append(f"  Duration:           {base_inputs.duration_years} years")
    lines.append(f"  Annual Return:      {base_inputs.annual_return:.1f}%")
    lines.append(f"  Annual Inflation:   {base_inputs.annual_inflation:.1f}%")
    lines.append("")

    for exp in [exp_a, exp_b, exp_c, exp_d]:
        lines.append("=" * 70)
        lines.append(f"EXPERIMENT {exp.experiment_id}: {exp.title}")
        lines.append("-" * 40)
        lines.append(f"  IV: {exp.independent_variable}")
        lines.append(f"  DV: {exp.dependent_variable}")
        lines.append("  Fixed Parameters:")
        for k, v in exp.fixed_parameters.items():
            lines.append(f"    {k}: {v}")
        lines.append(f"  Minimum Outcome: {format_currency_inr(exp.min_outcome)}")
        lines.append(f"  Maximum Outcome: {format_currency_inr(exp.max_outcome)}")
        lines.append(f"  Outcome Spread:  {format_currency_inr(exp.outcome_range)}")
        lines.append("")
        lines.append("  Interpretation:")
        # Word-wrap interpretation
        words = exp.interpretation.split()
        line = "    "
        for w in words:
            if len(line) + len(w) > 70:
                lines.append(line)
                line = "    " + w + " "
            else:
                line += w + " "
        lines.append(line)
        lines.append("")

    lines.append("=" * 70)
    lines.append("END OF EXPERIMENT SUMMARY REPORT")
    lines.append("Generated by WhatIf AI — B.Sc. AI & Data Science Capstone Project")
    lines.append("=" * 70)

    return "\n".join(lines)
