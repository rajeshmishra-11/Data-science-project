"""
Unit tests for scenario management, comparison report generation,
and trajectory data aggregation.
"""

import pytest
from src.calculations import SimulationInputs
from src.scenarios import (
    Scenario,
    get_default_preset_scenarios,
    compare_scenarios,
    build_multi_scenario_trajectory_dataframe,
)


def test_default_preset_scenarios():
    base_inputs = SimulationInputs(
        monthly_income=40000.0,
        essential_expenses=18000.0,
        discretionary_expenses=8000.0,
        current_savings=50000.0,
        monthly_contribution=8000.0,
        duration_years=5,
        annual_inflation=5.0,
        annual_return=6.0,
    )
    presets = get_default_preset_scenarios(base_inputs)

    assert len(presets) == 3
    names = [p.name for p in presets]
    assert "Current Plan" in names
    assert "Conservative Plan" in names
    assert "Improved Savings Plan" in names

    for p in presets:
        assert p.outputs is not None
        assert p.outputs.projected_ending_balance > 0


def test_scenario_comparison_report():
    base_inputs = SimulationInputs(
        monthly_income=40000.0,
        essential_expenses=18000.0,
        discretionary_expenses=8000.0,
        current_savings=50000.0,
        monthly_contribution=8000.0,
        duration_years=5,
    )
    presets = get_default_preset_scenarios(base_inputs)
    report = compare_scenarios(presets, baseline_id="current_plan")

    assert report.baseline_id == "current_plan"
    assert len(report.comparison_table) == 3
    assert "Projected_Ending_Balance" in report.comparison_table.columns
    assert "Delta_Ending_Balance" in report.comparison_table.columns
    assert len(report.insights) >= 1
    assert "highest_nominal" in report.rankings


def test_multi_scenario_trajectory_dataframe():
    presets = get_default_preset_scenarios()
    df = build_multi_scenario_trajectory_dataframe(presets)

    assert not df.empty
    assert "Scenario" in df.columns
    assert "Month" in df.columns
    assert "Nominal_Balance" in df.columns
    assert set(df["Scenario"].unique()) == {"Current Plan", "Conservative Plan", "Improved Savings Plan"}
