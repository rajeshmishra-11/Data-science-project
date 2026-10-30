"""
Sensitivity Analysis and Quantitative Risk Modeling for WhatIf AI.

Calculates:
- Multi-parameter sensitivity swings (Tornado chart dataset)
- Normalized point elasticity (% change in outcome / % change in input)
- One-dimensional parameter response sweeps (Contribution, Return, Duration, Inflation)
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
import pandas as pd
from src.calculations import SimulationInputs, calculate_simulation


@dataclass
class TornadoVariableResult:
    parameter_name: str
    display_name: str
    base_value: float
    low_value: float
    high_value: float
    low_outcome: float
    high_outcome: float
    outcome_swing: float  # abs(high_outcome - low_outcome)
    elasticity: float     # (% dOutcome) / (% dParam)


@dataclass
class SensitivityReport:
    base_outcome: float
    tornado_results: List[TornadoVariableResult]
    ranked_by_impact: List[TornadoVariableResult]
    top_driver_name: str
    top_driver_swing: float
    insights: List[str]


def compute_tornado_analysis(
    base_inputs: SimulationInputs,
    perturbation_pct: float = 20.0
) -> SensitivityReport:
    """
    Computes a Tornado Sensitivity Analysis by varying key input parameters by +/- perturbation_pct
    (or appropriate standard deltas) while holding all other parameters constant (ceteris paribus).
    """
    base_out = calculate_simulation(base_inputs)
    base_ending = base_out.projected_ending_balance

    # Define test parameters and their deltas
    # For percentages, we do absolute percentage point shifts (e.g. +/- 2% or +/- 3%)
    # For amounts, we do percentage swings
    p_frac = perturbation_pct / 100.0

    variables = [
        {
            "name": "monthly_contribution",
            "display": "Monthly Contribution",
            "base": base_inputs.monthly_contribution,
            "low": max(0.0, base_inputs.monthly_contribution * (1.0 - p_frac)),
            "high": base_inputs.monthly_contribution * (1.0 + p_frac),
            "is_pct": False,
        },
        {
            "name": "annual_return",
            "display": "Assumed Return Rate",
            "base": base_inputs.annual_return,
            "low": max(0.0, base_inputs.annual_return - 3.0),
            "high": base_inputs.annual_return + 3.0,
            "is_pct": True,
        },
        {
            "name": "duration_years",
            "display": "Simulation Duration",
            "base": float(base_inputs.duration_years),
            "low": max(1.0, float(base_inputs.duration_years - 2)),
            "high": float(base_inputs.duration_years + 2),
            "is_pct": False,
        },
        {
            "name": "current_savings",
            "display": "Initial Savings Balance",
            "base": base_inputs.current_savings,
            "low": max(0.0, base_inputs.current_savings * (1.0 - p_frac)),
            "high": base_inputs.current_savings * (1.0 + p_frac),
            "is_pct": False,
        },
        {
            "name": "annual_inflation",
            "display": "Annual Inflation (Real Purchasing Power)",
            "base": base_inputs.annual_inflation,
            "low": max(0.0, base_inputs.annual_inflation - 2.0),
            "high": base_inputs.annual_inflation + 2.0,
            "is_pct": True,
            "measure": "real_balance",  # Inflation primarily impacts real purchasing power
        },
    ]

    results: List[TornadoVariableResult] = []

    for v in variables:
        # Evaluate Low Case
        low_inputs = SimulationInputs(
            monthly_income=base_inputs.monthly_income,
            essential_expenses=base_inputs.essential_expenses,
            discretionary_expenses=base_inputs.discretionary_expenses,
            current_savings=v["low"] if v["name"] == "current_savings" else base_inputs.current_savings,
            monthly_contribution=v["low"] if v["name"] == "monthly_contribution" else base_inputs.monthly_contribution,
            duration_years=int(v["low"]) if v["name"] == "duration_years" else base_inputs.duration_years,
            annual_inflation=v["low"] if v["name"] == "annual_inflation" else base_inputs.annual_inflation,
            annual_return=v["low"] if v["name"] == "annual_return" else base_inputs.annual_return,
            contribution_timing=base_inputs.contribution_timing,
        )
        low_out = calculate_simulation(low_inputs)
        low_val = low_out.inflation_adjusted_balance if v.get("measure") == "real_balance" else low_out.projected_ending_balance

        # Evaluate High Case
        high_inputs = SimulationInputs(
            monthly_income=base_inputs.monthly_income,
            essential_expenses=base_inputs.essential_expenses,
            discretionary_expenses=base_inputs.discretionary_expenses,
            current_savings=v["high"] if v["name"] == "current_savings" else base_inputs.current_savings,
            monthly_contribution=v["high"] if v["name"] == "monthly_contribution" else base_inputs.monthly_contribution,
            duration_years=int(v["high"]) if v["name"] == "duration_years" else base_inputs.duration_years,
            annual_inflation=v["high"] if v["name"] == "annual_inflation" else base_inputs.annual_inflation,
            annual_return=v["high"] if v["name"] == "annual_return" else base_inputs.annual_return,
            contribution_timing=base_inputs.contribution_timing,
        )
        high_out = calculate_simulation(high_inputs)
        high_val = high_out.inflation_adjusted_balance if v.get("measure") == "real_balance" else high_out.projected_ending_balance

        swing = abs(high_val - low_val)

        # Calculate arc elasticity: (% dOutcome) / (% dParam)
        param_diff = (v["high"] - v["low"])
        param_mid = (v["high"] + v["low"]) / 2.0 if (v["high"] + v["low"]) > 0 else 1.0
        pct_dparam = (param_diff / param_mid) if param_mid > 0 else 1.0

        outcome_mid = (high_val + low_val) / 2.0 if (high_val + low_val) > 0 else 1.0
        pct_doutcome = (swing / outcome_mid) if outcome_mid > 0 else 0.0

        elasticity = round(pct_doutcome / pct_dparam, 3) if pct_dparam > 0 else 0.0

        results.append(
            TornadoVariableResult(
                parameter_name=v["name"],
                display_name=v["display"],
                base_value=v["base"],
                low_value=v["low"],
                high_value=v["high"],
                low_outcome=low_val,
                high_outcome=high_val,
                outcome_swing=swing,
                elasticity=elasticity,
            )
        )

    # Sort descending by impact (swing)
    ranked = sorted(results, key=lambda x: x.outcome_swing, reverse=True)
    top_driver = ranked[0]

    insights = [
        f"**Primary Driver**: **{top_driver.display_name}** creates the largest numerical swing ({top_driver.outcome_swing:,.0f} INR) in projected outcome under local perturbations.",
        f"**Contribution Sensitivity**: Modifying monthly contribution directly shifts your guaranteed principal base before any return compounding.",
        f"**Time Horizon Non-Linearity**: As duration extends beyond 5 years, sensitivity to assumed return rates escalates exponentially due to compound interest.",
    ]

    return SensitivityReport(
        base_outcome=base_ending,
        tornado_results=results,
        ranked_by_impact=ranked,
        top_driver_name=top_driver.display_name,
        top_driver_swing=top_driver.outcome_swing,
        insights=insights,
    )


def compute_1d_sweep_contribution(
    base_inputs: SimulationInputs,
    min_contrib: float = 1000.0,
    max_contrib: float = 30000.0,
    steps: int = 15
) -> pd.DataFrame:
    """
    Computes ending balance across an array of monthly contribution amounts.
    """
    step_size = (max_contrib - min_contrib) / max(1, steps - 1)
    rows = []
    for s in range(steps):
        contrib = min_contrib + s * step_size
        test_inputs = SimulationInputs(
            monthly_income=base_inputs.monthly_income,
            essential_expenses=base_inputs.essential_expenses,
            discretionary_expenses=base_inputs.discretionary_expenses,
            current_savings=base_inputs.current_savings,
            monthly_contribution=contrib,
            duration_years=base_inputs.duration_years,
            annual_inflation=base_inputs.annual_inflation,
            annual_return=base_inputs.annual_return,
            contribution_timing=base_inputs.contribution_timing,
        )
        out = calculate_simulation(test_inputs)
        rows.append({
            "Monthly_Contribution": round(contrib, -2),
            "Ending_Balance": out.projected_ending_balance,
            "Total_Contributed": out.total_contributed,
            "Estimated_Growth": out.estimated_growth,
            "Real_Value": out.inflation_adjusted_balance,
            "Savings_Rate": out.savings_rate,
        })
    return pd.DataFrame(rows)


def compute_1d_sweep_returns(
    base_inputs: SimulationInputs,
    min_return: float = 0.0,
    max_return: float = 15.0,
    steps: int = 16
) -> pd.DataFrame:
    """
    Computes ending balance across varying annual return rates.
    """
    step_size = (max_return - min_return) / max(1, steps - 1)
    rows = []
    for s in range(steps):
        ret = min_return + s * step_size
        test_inputs = SimulationInputs(
            monthly_income=base_inputs.monthly_income,
            essential_expenses=base_inputs.essential_expenses,
            discretionary_expenses=base_inputs.discretionary_expenses,
            current_savings=base_inputs.current_savings,
            monthly_contribution=base_inputs.monthly_contribution,
            duration_years=base_inputs.duration_years,
            annual_inflation=base_inputs.annual_inflation,
            annual_return=ret,
            contribution_timing=base_inputs.contribution_timing,
        )
        out = calculate_simulation(test_inputs)
        rows.append({
            "Annual_Return": round(ret, 1),
            "Ending_Balance": out.projected_ending_balance,
            "Total_Contributed": out.total_contributed,
            "Estimated_Growth": out.estimated_growth,
            "Real_Value": out.inflation_adjusted_balance,
        })
    return pd.DataFrame(rows)
