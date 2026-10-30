"""
Unit tests for core financial calculations, compounding, inflation discounting,
and edge case validation.
"""

import pytest
import math
from src.calculations import (
    SimulationInputs,
    validate_inputs,
    calculate_simulation,
    generate_monthly_schedule,
    generate_yearly_schedule,
    calculate_target_feasibility,
    format_currency_inr,
)


def test_zero_return_savings_calculation():
    """
    Verifies that with 0% return:
    Ending Balance = Current Savings + Monthly Contribution * (Years * 12)
    """
    inputs = SimulationInputs(
        monthly_income=50000.0,
        essential_expenses=20000.0,
        discretionary_expenses=10000.0,
        current_savings=100000.0,
        monthly_contribution=10000.0,
        duration_years=5,
        annual_inflation=0.0,
        annual_return=0.0,
    )
    outputs = calculate_simulation(inputs)

    expected_contributions = 10000.0 * 5 * 12  # 600,000
    expected_ending_balance = 100000.0 + expected_contributions  # 700,000

    assert outputs.total_months == 60
    assert pytest.approx(outputs.total_contributed, rel=1e-5) == expected_contributions
    assert pytest.approx(outputs.projected_ending_balance, rel=1e-5) == expected_ending_balance
    assert outputs.estimated_growth == 0.0
    assert pytest.approx(outputs.inflation_adjusted_balance, rel=1e-5) == expected_ending_balance


def test_nonzero_return_compounding():
    """
    Verifies compound interest with 12% annual return (1% monthly):
    FV_lump = PV * (1 + r)^n
    FV_annuity = PMT * ((1 + r)^n - 1) / r
    """
    pv = 50000.0
    pmt = 5000.0
    years = 2
    n = years * 12
    r_annual = 12.0
    r_monthly = (r_annual / 100.0) / 12.0  # 0.01

    inputs = SimulationInputs(
        monthly_income=40000.0,
        essential_expenses=18000.0,
        discretionary_expenses=8000.0,
        current_savings=pv,
        monthly_contribution=pmt,
        duration_years=years,
        annual_inflation=0.0,
        annual_return=r_annual,
        contribution_timing="end",
    )
    outputs = calculate_simulation(inputs)

    expected_fv_lump = pv * ((1.0 + r_monthly) ** n)
    expected_fv_annuity = pmt * (((1.0 + r_monthly) ** n - 1.0) / r_monthly)
    expected_total = expected_fv_lump + expected_fv_annuity

    assert pytest.approx(outputs.projected_ending_balance, rel=1e-5) == expected_total
    assert outputs.estimated_growth > 0
    assert pytest.approx(outputs.estimated_growth, rel=1e-5) == (expected_total - (pv + pmt * n))


def test_inflation_adjustment():
    """
    Verifies inflation discounting: Real FV = FV / (1 + i)^t
    """
    inputs = SimulationInputs(
        monthly_income=40000.0,
        essential_expenses=18000.0,
        discretionary_expenses=8000.0,
        current_savings=50000.0,
        monthly_contribution=8000.0,
        duration_years=5,
        annual_inflation=6.0,
        annual_return=0.0,
    )
    outputs = calculate_simulation(inputs)

    nominal_ending = outputs.projected_ending_balance
    expected_real = nominal_ending / ((1.0 + 0.06) ** 5)

    assert pytest.approx(outputs.inflation_adjusted_balance, rel=1e-5) == expected_real
    assert outputs.purchasing_power_loss > 0
    assert pytest.approx(outputs.purchasing_power_loss, rel=1e-5) == (nominal_ending - expected_real)


def test_validation_warnings_surplus():
    """
    Verifies validation flags when contribution exceeds available surplus or expenses exceed income.
    """
    # Case 1: Contribution exceeds surplus
    inputs = SimulationInputs(
        monthly_income=30000.0,
        essential_expenses=15000.0,
        discretionary_expenses=10000.0,
        current_savings=10000.0,
        monthly_contribution=8000.0,  # Surplus is 5,000
    )
    val = validate_inputs(inputs)
    assert val.is_valid
    assert val.monthly_surplus == 5000.0
    assert any("exceeds your available monthly surplus" in w for w in val.warnings)

    # Case 2: Expenses exceed income (deficit)
    deficit_inputs = SimulationInputs(
        monthly_income=25000.0,
        essential_expenses=20000.0,
        discretionary_expenses=10000.0,
        current_savings=5000.0,
        monthly_contribution=2000.0,
    )
    def_val = validate_inputs(deficit_inputs)
    assert def_val.monthly_surplus == -5000.0
    assert any("exceed your monthly income" in w for w in def_val.warnings)


def test_zero_income_and_zero_savings_edge_case():
    """
    Tests edge cases with zeros.
    """
    inputs = SimulationInputs(
        monthly_income=0.0,
        essential_expenses=0.0,
        discretionary_expenses=0.0,
        current_savings=0.0,
        monthly_contribution=0.0,
        duration_years=3,
        annual_inflation=5.0,
        annual_return=10.0,
    )
    outputs = calculate_simulation(inputs)
    assert outputs.projected_ending_balance == 0.0
    assert outputs.total_contributed == 0.0
    assert outputs.estimated_growth == 0.0
    assert outputs.inflation_adjusted_balance == 0.0
    assert outputs.savings_rate == 0.0


def test_target_feasibility_achieved_and_shortfall():
    """
    Tests break-even / target feasibility calculations.
    """
    inputs = SimulationInputs(
        monthly_income=50000.0,
        essential_expenses=20000.0,
        discretionary_expenses=10000.0,
        current_savings=50000.0,
        monthly_contribution=10000.0,
        duration_years=5,
        annual_inflation=5.0,
        annual_return=0.0,
    )
    # Total projected is 50,000 + 10,000 * 60 = 650,000

    # Target 500,000 is achieved
    res_achieved = calculate_target_feasibility(inputs, target_amount=500000.0)
    assert res_achieved.target_achieved is True
    assert res_achieved.surplus_or_shortfall == 150000.0

    # Target 1,000,000 requires more contributions
    res_shortfall = calculate_target_feasibility(inputs, target_amount=1000000.0)
    assert res_shortfall.target_achieved is False
    assert res_shortfall.surplus_or_shortfall == -350000.0
    # Required PMT = (1,000,000 - 50,000) / 60 = 15,833.33
    assert pytest.approx(res_shortfall.required_monthly_contribution, rel=1e-3) == (950000.0 / 60)
    # Available surplus is 20,000, so required 15,833 is feasible
    assert res_shortfall.is_feasible_with_surplus is True


def test_monthly_and_yearly_schedules():
    """
    Tests schedule generation consistency.
    """
    inputs = SimulationInputs(
        monthly_income=40000.0,
        essential_expenses=18000.0,
        discretionary_expenses=8000.0,
        current_savings=50000.0,
        monthly_contribution=8000.0,
        duration_years=3,
        annual_inflation=5.0,
        annual_return=6.0,
    )
    m_df = generate_monthly_schedule(inputs)
    assert len(m_df) == 36
    assert m_df["Month"].iloc[-1] == 36
    assert m_df["Closing_Balance"].iloc[-1] > 50000.0

    y_df = generate_yearly_schedule(inputs)
    assert len(y_df) == 3
    assert y_df["Year"].tolist() == [1, 2, 3]
    assert pytest.approx(y_df["Ending_Balance"].iloc[-1], rel=1e-4) == m_df["Closing_Balance"].iloc[-1]


def test_inr_formatting():
    """
    Tests Indian rupee number grouping.
    """
    assert format_currency_inr(0) == "₹0"
    assert format_currency_inr(500) == "₹500"
    assert format_currency_inr(1500) == "₹1,500"
    assert format_currency_inr(50000) == "₹50,000"
    assert format_currency_inr(1000000) == "₹10,00,000"
    assert format_currency_inr(-25000) == "-₹25,000"
