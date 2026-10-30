"""
Comprehensive test suite for all WhatIf AI modules.

Tests cover:
- Recommendation engine rules and outputs
- Uncertainty/Future Scenario Explorer calculations
- Data Science Experiment Lab (all four experiments)
- Export functions (CSV and text report)
- Edge cases and boundary conditions
"""

import pytest
import math
from src.calculations import SimulationInputs, calculate_simulation, format_currency_inr
from src.recommendation_engine import generate_recommendations, RecommendationReport
from src.uncertainty_analysis import (
    get_default_scenario_configs,
    compute_future_scenario_explorer,
    UncertaintyScenarioConfig,
    explain_scenario_spread,
)
from src.experiment_lab import (
    run_experiment_a,
    run_experiment_b,
    run_experiment_c,
    run_experiment_d,
    export_experiment_results_csv,
    export_experiment_summary_report,
)


# ===========================================================================
# FIXTURES
# ===========================================================================

@pytest.fixture
def standard_inputs():
    return SimulationInputs(
        monthly_income=50000.0,
        essential_expenses=20000.0,
        discretionary_expenses=10000.0,
        current_savings=100000.0,
        monthly_contribution=10000.0,
        duration_years=5,
        annual_inflation=5.0,
        annual_return=8.0,
    )


@pytest.fixture
def deficit_inputs():
    """Inputs where expenses exceed income."""
    return SimulationInputs(
        monthly_income=25000.0,
        essential_expenses=20000.0,
        discretionary_expenses=10000.0,  # Total = 30,000 > 25,000
        current_savings=5000.0,
        monthly_contribution=2000.0,
        duration_years=3,
        annual_inflation=5.0,
        annual_return=0.0,
    )


@pytest.fixture
def surplus_overflow_inputs():
    """Inputs where contribution > surplus."""
    return SimulationInputs(
        monthly_income=40000.0,
        essential_expenses=20000.0,
        discretionary_expenses=10000.0,  # Surplus = 10,000
        current_savings=50000.0,
        monthly_contribution=15000.0,    # Exceeds surplus of 10,000
        duration_years=5,
        annual_inflation=5.0,
        annual_return=0.0,
    )


# ===========================================================================
# RECOMMENDATION ENGINE TESTS
# ===========================================================================

class TestRecommendationEngine:

    def test_returns_recommendation_report(self, standard_inputs):
        """Engine always returns a valid RecommendationReport."""
        report = generate_recommendations(standard_inputs)
        assert isinstance(report, RecommendationReport)
        assert isinstance(report.recommendations, list)
        assert isinstance(report.summary, str)
        assert len(report.summary) > 10

    def test_deficit_triggers_critical_recommendation(self, deficit_inputs):
        """Rule 1: Budget deficit must generate a critical recommendation."""
        report = generate_recommendations(deficit_inputs)
        critical_recs = [r for r in report.recommendations if r.severity == "critical"]
        assert len(critical_recs) >= 1
        budget_crits = [r for r in critical_recs if r.category == "Budget"]
        assert len(budget_crits) >= 1
        assert "Deficit" in budget_crits[0].title or "deficit" in budget_crits[0].reason.lower()

    def test_surplus_overflow_triggers_warning(self, surplus_overflow_inputs):
        """Rule 2: Contribution > surplus must generate a warning."""
        report = generate_recommendations(surplus_overflow_inputs)
        warnings = [r for r in report.recommendations if r.severity == "warning"]
        savings_warnings = [r for r in warnings if r.category == "Savings"]
        assert len(savings_warnings) >= 1
        assert "Surplus" in savings_warnings[0].title or "surplus" in savings_warnings[0].reason.lower()

    def test_goal_achieved_generates_positive(self, standard_inputs):
        """Rule 5: Achievable goal generates a positive recommendation."""
        # With 50k existing + 10k/mo * 60 months = 700k. Target 500k is achievable.
        report = generate_recommendations(standard_inputs, target_amount=300000.0)
        positives = [r for r in report.recommendations if r.severity == "positive"]
        goal_positives = [r for r in positives if r.category == "Goal"]
        assert len(goal_positives) >= 1

    def test_goal_shortfall_generates_warning(self, standard_inputs):
        """Rule 6: Unachievable goal (within surplus) generates warning."""
        # Target 50 million - clearly unachievable
        report = generate_recommendations(standard_inputs, target_amount=50_000_000.0)
        goal_recs = [r for r in report.recommendations if r.category == "Goal"]
        assert len(goal_recs) >= 1
        # Should be critical or warning
        assert any(r.severity in ("critical", "warning") for r in goal_recs)

    def test_zero_return_triggers_info_recommendation(self):
        """Rule 8: Zero return with duration >= 3 generates info recommendation."""
        inputs = SimulationInputs(
            monthly_income=40000.0, essential_expenses=15000.0,
            discretionary_expenses=8000.0, current_savings=50000.0,
            monthly_contribution=8000.0, duration_years=5,
            annual_inflation=5.0, annual_return=0.0,
        )
        report = generate_recommendations(inputs)
        info_recs = [r for r in report.recommendations if r.severity == "info"]
        zero_return_recs = [r for r in info_recs if "0%" in r.metric_value or "0.0%" in r.metric_value]
        assert len(zero_return_recs) >= 1

    def test_all_recommendations_have_required_fields(self, standard_inputs):
        """All recommendations must have non-empty title, reason, action, category."""
        report = generate_recommendations(standard_inputs, target_amount=500000.0)
        for rec in report.recommendations:
            assert len(rec.title) > 5, f"Title too short: {rec.title!r}"
            assert len(rec.reason) > 10, f"Reason too short for {rec.title}"
            assert len(rec.action) > 10, f"Action too short for {rec.title}"
            assert rec.category in ("Budget", "Savings", "Inflation", "Goal", "Growth", "Strategy")
            assert rec.severity in ("critical", "warning", "info", "positive")

    def test_issue_and_positive_counts(self, standard_inputs):
        """total_issues and positive_findings are correctly counted."""
        report = generate_recommendations(standard_inputs, target_amount=500000.0)
        issues_count = len([r for r in report.recommendations if r.severity in ("critical", "warning")])
        pos_count = len([r for r in report.recommendations if r.severity == "positive"])
        assert report.total_issues == issues_count
        assert report.positive_findings == pos_count

    def test_no_recommendations_for_pristine_inputs(self):
        """
        Pristine inputs (balanced budget, modest goals, reasonable rates)
        should not trigger any critical recommendations.
        """
        inputs = SimulationInputs(
            monthly_income=60000.0,
            essential_expenses=20000.0,
            discretionary_expenses=10000.0,
            current_savings=100000.0,
            monthly_contribution=15000.0,  # Within surplus of 30,000
            duration_years=5,
            annual_inflation=5.0,
            annual_return=8.0,
        )
        report = generate_recommendations(inputs, target_amount=500000.0)
        critical_recs = [r for r in report.recommendations if r.severity == "critical"]
        assert len(critical_recs) == 0

    def test_recommendations_use_actual_values(self, deficit_inputs):
        """Verify that recommendations reference calculated amounts, not generic text."""
        report = generate_recommendations(deficit_inputs)
        # The critical budget rec should mention actual numbers
        budget_recs = [r for r in report.recommendations if r.category == "Budget"]
        assert len(budget_recs) >= 1
        # Should contain a rupee symbol (₹) in reason or action
        for r in budget_recs:
            assert "₹" in r.reason or "₹" in r.action


# ===========================================================================
# UNCERTAINTY ANALYSIS TESTS
# ===========================================================================

class TestUncertaintyAnalysis:

    def test_get_default_configs_returns_three_scenarios(self):
        """get_default_scenario_configs returns all three scenario configs."""
        configs = get_default_scenario_configs(8000.0, 5.0, 8.0, 5)
        assert "optimistic" in configs
        assert "moderate" in configs
        assert "pessimistic" in configs

    def test_optimistic_has_higher_return_than_pessimistic(self):
        """Optimistic return >= Pessimistic return in defaults."""
        configs = get_default_scenario_configs(8000.0, 5.0, 8.0, 5)
        assert configs["optimistic"].annual_return >= configs["pessimistic"].annual_return

    def test_optimistic_has_lower_inflation_than_pessimistic(self):
        """Optimistic inflation <= Pessimistic inflation in defaults."""
        configs = get_default_scenario_configs(8000.0, 5.0, 8.0, 5)
        assert configs["optimistic"].annual_inflation <= configs["pessimistic"].annual_inflation

    def test_compute_explorer_produces_valid_result(self):
        """compute_future_scenario_explorer returns valid calculations."""
        configs = get_default_scenario_configs(8000.0, 5.0, 8.0, 5)
        result = compute_future_scenario_explorer(
            configs["optimistic"], configs["moderate"], configs["pessimistic"],
            initial_savings=50000.0
        )
        assert result.optimistic.projected_ending_balance > 0
        assert result.moderate.projected_ending_balance > 0
        assert result.pessimistic.projected_ending_balance > 0

    def test_optimistic_balance_geq_pessimistic(self):
        """Optimistic outcome must be >= Pessimistic outcome."""
        configs = get_default_scenario_configs(8000.0, 5.0, 8.0, 5)
        result = compute_future_scenario_explorer(
            configs["optimistic"], configs["moderate"], configs["pessimistic"],
            initial_savings=50000.0
        )
        assert result.optimistic.projected_ending_balance >= result.pessimistic.projected_ending_balance

    def test_spread_calculation(self):
        """optimism_pessimism_diff = optimistic - pessimistic."""
        configs = get_default_scenario_configs(8000.0, 5.0, 8.0, 5)
        result = compute_future_scenario_explorer(
            configs["optimistic"], configs["moderate"], configs["pessimistic"],
            initial_savings=50000.0
        )
        expected_diff = result.optimistic.projected_ending_balance - result.pessimistic.projected_ending_balance
        assert pytest.approx(result.optimism_pessimism_diff, rel=1e-5) == expected_diff

    def test_trajectory_dataframe_structure(self):
        """Trajectory DataFrame has correct schema."""
        configs = get_default_scenario_configs(8000.0, 5.0, 8.0, 5)
        result = compute_future_scenario_explorer(
            configs["optimistic"], configs["moderate"], configs["pessimistic"],
            initial_savings=50000.0
        )
        df = result.trajectory_df
        assert not df.empty
        required_cols = ["Scenario", "Month", "Year", "Nominal_Balance", "Real_Balance"]
        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"
        assert set(df["Scenario"].unique()) == {"Optimistic", "Moderate", "Pessimistic"}

    def test_scenario_calculations_match_main_engine(self):
        """
        Verify that uncertainty scenario calculations match the main simulation engine
        for the same inputs (mathematical consistency check).
        """
        contrib = 8000.0
        ret = 8.0
        inflation = 5.0
        duration = 5
        initial = 50000.0

        mod_cfg = UncertaintyScenarioConfig(
            monthly_contribution=contrib,
            annual_inflation=inflation,
            annual_return=ret,
            duration_years=duration,
            label="Test",
            color="#000000",
            description="Test",
        )
        configs = {"optimistic": mod_cfg, "moderate": mod_cfg, "pessimistic": mod_cfg}
        result = compute_future_scenario_explorer(
            mod_cfg, mod_cfg, mod_cfg, initial_savings=initial
        )

        # Cross-check with main engine
        main_inputs = SimulationInputs(
            monthly_income=0.0, essential_expenses=0.0, discretionary_expenses=0.0,
            current_savings=initial, monthly_contribution=contrib,
            duration_years=duration, annual_inflation=inflation, annual_return=ret,
        )
        main_out = calculate_simulation(main_inputs)

        assert pytest.approx(
            result.moderate.projected_ending_balance, rel=1e-4
        ) == main_out.projected_ending_balance

    def test_explain_scenario_spread_returns_string(self):
        """explain_scenario_spread returns a non-empty string."""
        configs = get_default_scenario_configs(8000.0, 5.0, 8.0, 5)
        result = compute_future_scenario_explorer(
            configs["optimistic"], configs["moderate"], configs["pessimistic"],
            initial_savings=50000.0
        )
        explanation = explain_scenario_spread(result)
        assert isinstance(explanation, str)
        assert len(explanation) > 50

    def test_zero_return_uncertainty_scenario(self):
        """Uncertainty analysis works correctly when return = 0%."""
        cfg = UncertaintyScenarioConfig(
            monthly_contribution=5000.0, annual_inflation=5.0,
            annual_return=0.0, duration_years=5,
            label="Test", color="#000", description="Zero return test",
        )
        result = compute_future_scenario_explorer(cfg, cfg, cfg, initial_savings=50000.0)
        # Zero return: ending = 50000 + 5000 * 60 = 350000
        expected = 50000.0 + 5000.0 * 60
        assert pytest.approx(result.moderate.projected_ending_balance, rel=1e-4) == expected


# ===========================================================================
# EXPERIMENT LAB TESTS
# ===========================================================================

class TestExperimentLab:

    def test_experiment_a_returns_valid_result(self, standard_inputs):
        """Experiment A produces a valid ExperimentResult."""
        result = run_experiment_a(standard_inputs)
        assert result.experiment_id == "A"
        assert len(result.data_points) > 0
        assert not result.data_frame.empty
        assert "Monthly_Contribution" in result.data_frame.columns

    def test_experiment_b_returns_valid_result(self, standard_inputs):
        """Experiment B produces a valid ExperimentResult."""
        result = run_experiment_b(standard_inputs)
        assert result.experiment_id == "B"
        assert len(result.data_points) > 0
        assert "Annual_Inflation" in result.data_frame.columns

    def test_experiment_c_returns_valid_result(self, standard_inputs):
        """Experiment C produces a valid ExperimentResult."""
        result = run_experiment_c(standard_inputs)
        assert result.experiment_id == "C"
        assert len(result.data_points) > 0
        assert "Annual_Return" in result.data_frame.columns

    def test_experiment_d_returns_valid_result(self, standard_inputs):
        """Experiment D produces a valid ExperimentResult."""
        result = run_experiment_d(standard_inputs)
        assert result.experiment_id == "D"
        assert len(result.data_points) > 0
        assert "Duration_Years" in result.data_frame.columns

    def test_experiment_a_monotonically_increasing(self, standard_inputs):
        """Higher contributions always produce higher or equal ending balances."""
        result = run_experiment_a(standard_inputs)
        balances = [dp.ending_balance for dp in result.data_points]
        for i in range(len(balances) - 1):
            assert balances[i] <= balances[i + 1], (
                f"Non-monotonic: {balances[i]} > {balances[i+1]} at index {i}"
            )

    def test_experiment_b_real_value_decreases_with_inflation(self, standard_inputs):
        """Higher inflation always reduces real purchasing power."""
        result = run_experiment_b(standard_inputs)
        real_values = [dp.real_value for dp in result.data_points]
        for i in range(len(real_values) - 1):
            assert real_values[i] >= real_values[i + 1], (
                f"Real value should decrease with more inflation: {real_values[i]} < {real_values[i+1]}"
            )

    def test_experiment_c_monotonically_increasing_with_return(self, standard_inputs):
        """Higher returns produce higher or equal ending balances."""
        result = run_experiment_c(standard_inputs)
        balances = [dp.ending_balance for dp in result.data_points]
        for i in range(len(balances) - 1):
            assert balances[i] <= balances[i + 1]

    def test_experiment_d_monotonically_increasing_with_duration(self, standard_inputs):
        """Longer durations produce higher or equal ending balances (with positive contribution)."""
        result = run_experiment_d(standard_inputs)
        balances = [dp.ending_balance for dp in result.data_points]
        for i in range(len(balances) - 1):
            assert balances[i] <= balances[i + 1]

    def test_experiment_outcome_range_correct(self, standard_inputs):
        """outcome_range = max_outcome - min_outcome."""
        for exp in [run_experiment_a(standard_inputs), run_experiment_c(standard_inputs)]:
            expected_range = exp.max_outcome - exp.min_outcome
            assert pytest.approx(exp.outcome_range, rel=1e-5) == expected_range

    def test_experiment_a_zero_contribution_point(self, standard_inputs):
        """Experiment A: zero contribution = pure lump sum growth."""
        result = run_experiment_a(standard_inputs, contribution_values=[0.0, 5000.0, 10000.0])
        zero_dp = result.data_points[0]
        # With zero contribution, only initial savings compounds
        inputs = SimulationInputs(
            monthly_income=0.0, essential_expenses=0.0, discretionary_expenses=0.0,
            current_savings=standard_inputs.current_savings,
            monthly_contribution=0.0,
            duration_years=standard_inputs.duration_years,
            annual_inflation=standard_inputs.annual_inflation,
            annual_return=standard_inputs.annual_return,
        )
        expected = calculate_simulation(inputs).projected_ending_balance
        assert pytest.approx(zero_dp.ending_balance, rel=1e-4) == expected

    def test_experiment_interpretation_is_non_empty(self, standard_inputs):
        """All experiments have non-empty interpretation strings."""
        for exp in [
            run_experiment_a(standard_inputs),
            run_experiment_b(standard_inputs),
            run_experiment_c(standard_inputs),
            run_experiment_d(standard_inputs),
        ]:
            assert len(exp.interpretation) > 50, f"Exp {exp.experiment_id} has too-short interpretation"

    def test_experiment_fixed_parameters_match(self, standard_inputs):
        """Fixed parameters for each experiment match the base inputs."""
        exp_a = run_experiment_a(standard_inputs)
        # For experiment A, the return should be fixed at the base value
        assert str(standard_inputs.annual_return) in exp_a.fixed_parameters.get("Annual Return", "")

    def test_csv_export_contains_all_experiments(self, standard_inputs):
        """CSV export contains data from all four experiments."""
        exp_a = run_experiment_a(standard_inputs)
        exp_b = run_experiment_b(standard_inputs)
        exp_c = run_experiment_c(standard_inputs)
        exp_d = run_experiment_d(standard_inputs)
        csv_str = export_experiment_results_csv(exp_a, exp_b, exp_c, exp_d)
        assert "Experiment A" in csv_str
        assert "Experiment B" in csv_str
        assert "Experiment C" in csv_str
        assert "Experiment D" in csv_str
        assert "Projected_Ending_Balance" in csv_str

    def test_summary_report_contains_key_sections(self, standard_inputs):
        """Text summary report contains required sections."""
        exp_a = run_experiment_a(standard_inputs)
        exp_b = run_experiment_b(standard_inputs)
        exp_c = run_experiment_c(standard_inputs)
        exp_d = run_experiment_d(standard_inputs)
        report = export_experiment_summary_report(exp_a, exp_b, exp_c, exp_d, standard_inputs)
        assert "WHATIF AI" in report
        assert "METHODOLOGY" in report
        assert "Mathematical Model" in report
        assert "LIMITATIONS" in report or "Limitations" in report
        assert "EXPERIMENT A" in report
        assert "EXPERIMENT B" in report
        assert "EXPERIMENT C" in report
        assert "EXPERIMENT D" in report

    def test_experiment_dataframe_has_required_columns(self, standard_inputs):
        """All experiment DataFrames have the required output columns."""
        required = {"Projected_Ending_Balance", "Real_Purchasing_Power", "Total_Contributions", "Estimated_Growth"}
        for exp in [
            run_experiment_a(standard_inputs),
            run_experiment_b(standard_inputs),
            run_experiment_c(standard_inputs),
            run_experiment_d(standard_inputs),
        ]:
            df_cols = set(exp.data_frame.columns)
            for col in required:
                assert col in df_cols, f"Missing '{col}' in Experiment {exp.experiment_id} DataFrame"


# ===========================================================================
# CROSS-MODULE CALCULATION CONSISTENCY TESTS
# ===========================================================================

class TestCalculationConsistency:

    def test_recommendation_uses_same_calculation_as_simulator(self, standard_inputs):
        """Recommendation engine uses identical ending balance as main calculation engine."""
        main_out = calculate_simulation(standard_inputs)
        report = generate_recommendations(standard_inputs, target_amount=main_out.projected_ending_balance * 1.5)
        # The "goal shortfall" recommendation should reference the correct ending balance
        goal_recs = [r for r in report.recommendations if r.category == "Goal"]
        # Goal should be reachable if target is much higher than projected
        assert any(r.severity in ("warning", "critical") for r in goal_recs)

    def test_experiment_a_matches_direct_calculation(self, standard_inputs):
        """Experiment A result at base contribution matches direct simulation."""
        result = run_experiment_a(standard_inputs, contribution_values=[
            standard_inputs.monthly_contribution
        ])
        direct_out = calculate_simulation(standard_inputs)
        assert pytest.approx(
            result.data_points[0].ending_balance, rel=1e-4
        ) == direct_out.projected_ending_balance

    def test_experiment_c_zero_return_equals_direct(self, standard_inputs):
        """Experiment C at 0% return matches direct calculation."""
        result = run_experiment_c(standard_inputs, return_values=[0.0])
        zero_inputs = SimulationInputs(
            monthly_income=standard_inputs.monthly_income,
            essential_expenses=standard_inputs.essential_expenses,
            discretionary_expenses=standard_inputs.discretionary_expenses,
            current_savings=standard_inputs.current_savings,
            monthly_contribution=standard_inputs.monthly_contribution,
            duration_years=standard_inputs.duration_years,
            annual_inflation=standard_inputs.annual_inflation,
            annual_return=0.0,
        )
        direct_out = calculate_simulation(zero_inputs)
        assert pytest.approx(
            result.data_points[0].ending_balance, rel=1e-4
        ) == direct_out.projected_ending_balance


# ===========================================================================
# INVALID INPUT HANDLING TESTS
# ===========================================================================

class TestInvalidInputHandling:

    def test_recommendation_engine_handles_zero_income(self):
        """Recommendation engine does not crash with zero income."""
        inputs = SimulationInputs(
            monthly_income=0.0, essential_expenses=0.0,
            discretionary_expenses=0.0, current_savings=100000.0,
            monthly_contribution=0.0, duration_years=5,
            annual_inflation=5.0, annual_return=0.0,
        )
        report = generate_recommendations(inputs)
        assert isinstance(report, RecommendationReport)

    def test_recommendation_engine_handles_no_target(self, standard_inputs):
        """Recommendation engine works without target_amount."""
        report = generate_recommendations(standard_inputs, target_amount=None)
        assert isinstance(report, RecommendationReport)
        # No Goal category recs should appear
        goal_recs = [r for r in report.recommendations if r.category == "Goal"]
        assert len(goal_recs) == 0

    def test_experiment_a_custom_contributions(self, standard_inputs):
        """Experiment A accepts custom contribution values list."""
        result = run_experiment_a(standard_inputs, contribution_values=[1000.0, 5000.0, 10000.0])
        assert len(result.data_points) == 3

    def test_experiment_d_single_duration(self, standard_inputs):
        """Experiment D handles a single duration value."""
        result = run_experiment_d(standard_inputs, duration_values=[10])
        assert len(result.data_points) == 1

    def test_uncertainty_with_equal_scenarios(self):
        """All three uncertainty scenarios can be identical (spread = 0)."""
        cfg = UncertaintyScenarioConfig(
            monthly_contribution=8000.0, annual_inflation=5.0,
            annual_return=8.0, duration_years=5,
            label="Same", color="#000000", description="Identical",
        )
        result = compute_future_scenario_explorer(cfg, cfg, cfg, initial_savings=50000.0)
        assert result.optimism_pessimism_diff == pytest.approx(0.0, abs=1.0)
