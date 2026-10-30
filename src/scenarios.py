"""
Scenario Management and Comparative Modeling for WhatIf AI.

Enables multi-scenario comparison, dynamic narrative explanations,
baseline delta analysis, and criterion-based ranking.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import pandas as pd
from src.calculations import (
    SimulationInputs,
    SimulationOutputs,
    calculate_simulation,
    format_currency_inr,
    generate_monthly_schedule,
)


@dataclass
class Scenario:
    id: str
    name: str
    description: str
    inputs: SimulationInputs
    color: str = "#4f46e5"  # UI Accent color
    outputs: Optional[SimulationOutputs] = None

    def evaluate(self) -> SimulationOutputs:
        self.outputs = calculate_simulation(self.inputs)
        return self.outputs


@dataclass
class ScenarioComparisonReport:
    scenarios: List[Scenario]
    baseline_id: str
    comparison_table: pd.DataFrame
    insights: List[str]
    rankings: Dict[str, List[str]]


def get_default_preset_scenarios(base_inputs: Optional[SimulationInputs] = None) -> List[Scenario]:
    """
    Creates the 3 core preset scenarios dynamically derived from the user's base inputs.
    - Current Plan: Baseline user inputs
    - Conservative Plan: Lower return (or 0%), slightly lower contribution, higher inflation
    - Improved Savings Plan: Optimized expenses (e.g. 20% cut in discretionary), +25% savings contribution
    """
    if base_inputs is None:
        base_inputs = SimulationInputs()

    # 1. Current Plan
    curr_inputs = SimulationInputs(
        monthly_income=base_inputs.monthly_income,
        essential_expenses=base_inputs.essential_expenses,
        discretionary_expenses=base_inputs.discretionary_expenses,
        current_savings=base_inputs.current_savings,
        monthly_contribution=base_inputs.monthly_contribution,
        duration_years=base_inputs.duration_years,
        annual_inflation=base_inputs.annual_inflation,
        annual_return=base_inputs.annual_return,
        contribution_timing=base_inputs.contribution_timing,
    )

    # 2. Conservative Plan (Safer assumptions, lower returns, slightly higher inflation)
    cons_return = max(0.0, base_inputs.annual_return - 3.0) if base_inputs.annual_return > 3.0 else 0.0
    cons_inflation = base_inputs.annual_inflation + 1.5
    cons_contrib = max(1000.0, round(base_inputs.monthly_contribution * 0.8, -2))
    cons_inputs = SimulationInputs(
        monthly_income=base_inputs.monthly_income,
        essential_expenses=base_inputs.essential_expenses,
        discretionary_expenses=base_inputs.discretionary_expenses,
        current_savings=base_inputs.current_savings,
        monthly_contribution=cons_contrib,
        duration_years=base_inputs.duration_years,
        annual_inflation=cons_inflation,
        annual_return=cons_return,
        contribution_timing=base_inputs.contribution_timing,
    )

    # 3. Improved Savings Plan (Optimized discretionary expenses, disciplined higher contribution, moderate return)
    disc_reduction = base_inputs.discretionary_expenses * 0.20
    boosted_contrib = round(base_inputs.monthly_contribution + disc_reduction, -2)
    boosted_return = max(base_inputs.annual_return + 2.0, 7.0)
    imp_inputs = SimulationInputs(
        monthly_income=base_inputs.monthly_income,
        essential_expenses=base_inputs.essential_expenses,
        discretionary_expenses=max(0.0, base_inputs.discretionary_expenses - disc_reduction),
        current_savings=base_inputs.current_savings,
        monthly_contribution=boosted_contrib,
        duration_years=base_inputs.duration_years,
        annual_inflation=base_inputs.annual_inflation,
        annual_return=boosted_return,
        contribution_timing=base_inputs.contribution_timing,
    )

    scenarios = [
        Scenario(
            id="current_plan",
            name="Current Plan",
            description="Your active baseline assumptions and current monthly contribution target.",
            inputs=curr_inputs,
            color="#4f46e5",  # Indigo
        ),
        Scenario(
            id="conservative_plan",
            name="Conservative Plan",
            description="Defensive outlook with reduced returns, higher inflation buffer, and lower savings.",
            inputs=cons_inputs,
            color="#d97706",  # Amber
        ),
        Scenario(
            id="improved_plan",
            name="Improved Savings Plan",
            description="Optimized discretionary spending (+₹ savings) combined with structured compound growth.",
            inputs=imp_inputs,
            color="#10b981",  # Mint Emerald
        ),
    ]

    for s in scenarios:
        s.evaluate()

    return scenarios


def compare_scenarios(
    scenarios: List[Scenario],
    baseline_id: Optional[str] = None
) -> ScenarioComparisonReport:
    """
    Compares multiple scenarios side-by-side, computing deltas against a selected baseline.
    Generates dynamic narrative explanations and multi-criteria ranking.
    """
    if not scenarios:
        return ScenarioComparisonReport(
            scenarios=[],
            baseline_id="",
            comparison_table=pd.DataFrame(),
            insights=[],
            rankings={},
        )

    # Ensure all evaluated
    for s in scenarios:
        if s.outputs is None:
            s.evaluate()

    # Identify baseline
    if baseline_id is None or not any(s.id == baseline_id for s in scenarios):
        baseline_id = scenarios[0].id

    baseline_scenario = next(s for s in scenarios if s.id == baseline_id)
    baseline_out = baseline_scenario.outputs

    table_rows = []
    for s in scenarios:
        out = s.outputs
        diff_ending = out.projected_ending_balance - baseline_out.projected_ending_balance
        diff_contrib = out.total_contributed - baseline_out.total_contributed
        diff_real = out.inflation_adjusted_balance - baseline_out.inflation_adjusted_balance
        diff_pct = (
            (diff_ending / baseline_out.projected_ending_balance * 100.0)
            if baseline_out.projected_ending_balance > 0
            else 0.0
        )

        table_rows.append({
            "Scenario_ID": s.id,
            "Scenario_Name": s.name,
            "Monthly_Contribution": out.inputs.monthly_contribution,
            "Annual_Return": out.inputs.annual_return,
            "Annual_Inflation": out.inputs.annual_inflation,
            "Duration_Years": out.inputs.duration_years,
            "Total_Contributed": out.total_contributed,
            "Estimated_Growth": out.estimated_growth,
            "Projected_Ending_Balance": out.projected_ending_balance,
            "Real_Purchasing_Power": out.inflation_adjusted_balance,
            "Delta_Ending_Balance": diff_ending,
            "Delta_Ending_Pct": diff_pct,
            "Delta_Contributions": diff_contrib,
            "Delta_Real_Value": diff_real,
            "Savings_Rate": out.savings_rate,
            "Color": s.color,
        })

    comp_df = pd.DataFrame(table_rows)

    # Dynamic explainable insights
    insights = []
    for s in scenarios:
        if s.id == baseline_id:
            continue
        out = s.outputs
        diff_contrib_monthly = out.inputs.monthly_contribution - baseline_out.inputs.monthly_contribution
        total_diff_contributions = out.total_contributed - baseline_out.total_contributed
        ending_diff = out.projected_ending_balance - baseline_out.projected_ending_balance
        growth_diff = out.estimated_growth - baseline_out.estimated_growth

        if diff_contrib_monthly > 0:
            insight_text = (
                f"**{s.name} vs {baseline_scenario.name}**: Increasing your monthly contribution by "
                f"{format_currency_inr(diff_contrib_monthly)} adds {format_currency_inr(total_diff_contributions)} in direct deposits over "
                f"{out.inputs.duration_years} years. "
            )
            if growth_diff > 0:
                insight_text += (
                    f"Coupled with your assumed return of {out.inputs.annual_return:.1f}%, the compound growth adds an extra "
                    f"{format_currency_inr(growth_diff)}, yielding an overall advantage of {format_currency_inr(ending_diff)}."
                )
            else:
                insight_text += (
                    f"Resulting in a net projected advantage of {format_currency_inr(ending_diff)}."
                )
            insights.append(insight_text)
        elif diff_contrib_monthly < 0:
            insights.append(
                f"**{s.name} vs {baseline_scenario.name}**: Decreasing monthly contribution by "
                f"{format_currency_inr(abs(diff_contrib_monthly))} reduces total savings by {format_currency_inr(abs(total_diff_contributions))}, "
                f"resulting in a {format_currency_inr(abs(ending_diff))} lower ending corpus."
            )

    # Rankings
    rank_by_nominal = sorted(scenarios, key=lambda x: x.outputs.projected_ending_balance, reverse=True)
    rank_by_real = sorted(scenarios, key=lambda x: x.outputs.inflation_adjusted_balance, reverse=True)
    rank_by_rate = sorted(scenarios, key=lambda x: x.outputs.savings_rate, reverse=True)

    rankings = {
        "highest_nominal": [s.name for s in rank_by_nominal],
        "highest_real_purchasing_power": [s.name for s in rank_by_real],
        "highest_savings_rate": [s.name for s in rank_by_rate],
    }

    return ScenarioComparisonReport(
        scenarios=scenarios,
        baseline_id=baseline_id,
        comparison_table=comp_df,
        insights=insights,
        rankings=rankings,
    )


def build_multi_scenario_trajectory_dataframe(scenarios: List[Scenario]) -> pd.DataFrame:
    """
    Constructs a merged monthly timeline dataframe across all active scenarios for Plotly multi-line charting.
    """
    records = []
    for s in scenarios:
        sched = generate_monthly_schedule(s.inputs)
        for _, row in sched.iterrows():
            records.append({
                "Scenario": s.name,
                "Scenario_ID": s.id,
                "Month": int(row["Month"]),
                "Year": round(row["Month"] / 12.0, 2),
                "Nominal_Balance": row["Closing_Balance"],
                "Real_Balance": row["Real_Balance"],
                "Cumulative_Principal": row["Cumulative_Principal"],
                "Cumulative_Growth": row["Cumulative_Growth"],
            })

    return pd.DataFrame(records)
