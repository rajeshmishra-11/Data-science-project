"""
Unit tests for Tornado sensitivity analysis, elasticity metrics,
and 1D parameter sweeps.
"""

import pytest
from src.calculations import SimulationInputs
from src.sensitivity import (
    compute_tornado_analysis,
    compute_1d_sweep_contribution,
    compute_1d_sweep_returns,
)


def test_tornado_sensitivity_analysis():
    inputs = SimulationInputs(
        monthly_income=40000.0,
        essential_expenses=18000.0,
        discretionary_expenses=8000.0,
        current_savings=50000.0,
        monthly_contribution=8000.0,
        duration_years=5,
        annual_inflation=5.0,
        annual_return=8.0,
    )
    report = compute_tornado_analysis(inputs, perturbation_pct=25.0)

    assert report.base_outcome > 0
    assert len(report.tornado_results) == 5
    assert len(report.ranked_by_impact) == 5
    # Verify ranking is sorted descending
    swings = [r.outcome_swing for r in report.ranked_by_impact]
    assert swings == sorted(swings, reverse=True)
    assert report.top_driver_name != ""
    assert len(report.insights) >= 2


def test_1d_sweeps():
    inputs = SimulationInputs(
        monthly_income=40000.0,
        essential_expenses=18000.0,
        discretionary_expenses=8000.0,
        current_savings=50000.0,
        monthly_contribution=8000.0,
        duration_years=5,
        annual_inflation=5.0,
        annual_return=6.0,
    )
    # Contribution sweep
    df_contrib = compute_1d_sweep_contribution(inputs, min_contrib=2000.0, max_contrib=10000.0, steps=5)
    assert len(df_contrib) == 5
    assert df_contrib["Ending_Balance"].iloc[-1] > df_contrib["Ending_Balance"].iloc[0]

    # Return sweep
    df_return = compute_1d_sweep_returns(inputs, min_return=0.0, max_return=12.0, steps=5)
    assert len(df_return) == 5
    assert df_return["Ending_Balance"].iloc[-1] > df_return["Ending_Balance"].iloc[0]
