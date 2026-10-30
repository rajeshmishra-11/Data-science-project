"""
Intelligent Financial Recommendation Engine for WhatIf AI.

A rule-based recommendation engine that analyzes users' actual financial inputs
and calculated outputs to generate dynamic, evidence-based, actionable
recommendations.

Design Principles:
- Every recommendation uses actual calculated values from SimulationInputs/Outputs.
- Each recommendation includes a reason (why it was triggered) and a practical
  next-step action.
- No duplicate or generic messages.
- No external AI API or fabricated financial advice.
- Recommendations are deterministic and reproducible given the same inputs.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import math

from src.calculations import (
    SimulationInputs,
    SimulationOutputs,
    TargetFeasibilityResult,
    calculate_simulation,
    calculate_target_feasibility,
    format_currency_inr,
)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class Recommendation:
    """A single generated recommendation with full context."""
    category: str          # e.g. "Budget", "Savings", "Inflation", "Goal"
    severity: str          # "critical" | "warning" | "info" | "positive"
    title: str             # Short headline
    reason: str            # Why this recommendation was triggered
    action: str            # Concrete next step for the user
    metric_label: str = "" # Optional supporting metric label
    metric_value: str = "" # Optional supporting metric value


@dataclass
class RecommendationReport:
    """Full recommendation report from the engine."""
    recommendations: List[Recommendation]
    total_issues: int
    positive_findings: int
    summary: str           # One-sentence overall assessment


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _pct(value: float, total: float) -> float:
    """Safe percentage calculation, returns 0 if total is 0."""
    return (value / total * 100.0) if total > 0 else 0.0


# ---------------------------------------------------------------------------
# Core Recommendation Engine
# ---------------------------------------------------------------------------

def generate_recommendations(
    inputs: SimulationInputs,
    target_amount: Optional[float] = None,
) -> RecommendationReport:
    """
    Analyzes user financial inputs and produces a prioritized list of
    rule-based recommendations.

    Rules evaluated (in order of severity):
    1.  Deficit alert: total expenses exceed monthly income.
    2.  Contribution vs. surplus mismatch.
    3.  Discretionary spending ratio.
    4.  Savings rate assessment.
    5.  Goal feasibility (if target provided).
    6.  Goal already achievable confirmation.
    7.  Shortfall: additional contribution required.
    8.  Inflation drag on purchasing power.
    9.  Zero-return assumption notice.
    10. Duration extension opportunity.
    11. Large initial savings leverage.
    12. High savings-rate praise (positive reinforcement).
    """
    outputs: SimulationOutputs = calculate_simulation(inputs)
    recommendations: List[Recommendation] = []

    monthly_income = inputs.monthly_income
    essential = inputs.essential_expenses
    discretionary = inputs.discretionary_expenses
    total_expenses = outputs.total_expenses
    surplus = outputs.monthly_surplus
    contrib = inputs.monthly_contribution
    duration = inputs.duration_years
    inflation = inputs.annual_inflation
    ret_rate = inputs.annual_return
    ending = outputs.projected_ending_balance
    real_val = outputs.inflation_adjusted_balance
    pwr_loss = outputs.purchasing_power_loss
    savings_rate = outputs.savings_rate

    # ------------------------------------------------------------------
    # RULE 1 - Budget deficit: expenses > income
    # ------------------------------------------------------------------
    if total_expenses > monthly_income and monthly_income > 0:
        overspend = total_expenses - monthly_income
        recommendations.append(Recommendation(
            category="Budget",
            severity="critical",
            title="Monthly Budget is in Deficit",
            reason=(
                f"Your total monthly expenses ({format_currency_inr(total_expenses)}) exceed "
                f"your monthly income ({format_currency_inr(monthly_income)}) by "
                f"{format_currency_inr(overspend)}. Running a persistent deficit makes any "
                "savings target mathematically unsustainable without external funding."
            ),
            action=(
                f"Reduce either essential ({format_currency_inr(essential)}/mo) or "
                f"discretionary ({format_currency_inr(discretionary)}/mo) expenses by at least "
                f"{format_currency_inr(overspend)}/mo to achieve a balanced budget before "
                "implementing a savings plan."
            ),
            metric_label="Monthly Deficit",
            metric_value=format_currency_inr(overspend),
        ))

    # ------------------------------------------------------------------
    # RULE 2 - Contribution exceeds available surplus
    # ------------------------------------------------------------------
    elif surplus >= 0 and contrib > surplus:
        gap = contrib - surplus
        recommendations.append(Recommendation(
            category="Savings",
            severity="warning",
            title="Contribution Target Exceeds Available Monthly Surplus",
            reason=(
                f"Your chosen monthly contribution of {format_currency_inr(contrib)} exceeds "
                f"your actual monthly surplus of {format_currency_inr(surplus)} by "
                f"{format_currency_inr(gap)}. This means the savings plan cannot be consistently "
                "sustained on current income and spending alone."
            ),
            action=(
                f"Either reduce your monthly contribution to {format_currency_inr(surplus)} "
                f"(matching your surplus), or reduce discretionary spending by at least "
                f"{format_currency_inr(gap)}/mo to create the necessary headroom."
            ),
            metric_label="Contribution vs. Surplus Gap",
            metric_value=format_currency_inr(gap),
        ))

    # ------------------------------------------------------------------
    # RULE 3 - Discretionary spending disproportionate
    # ------------------------------------------------------------------
    disc_pct = _pct(discretionary, monthly_income)
    if monthly_income > 0 and disc_pct > 35.0:
        savings_boost = round(discretionary * 0.20)
        recommendations.append(Recommendation(
            category="Budget",
            severity="warning",
            title="Discretionary Spending Represents a High Fraction of Income",
            reason=(
                f"Discretionary expenses account for {disc_pct:.1f}% of your monthly income "
                f"({format_currency_inr(discretionary)}/mo). While spending decisions are personal, "
                "proportions above 35% may indicate room for reallocation toward long-term savings."
            ),
            action=(
                "Consider reviewing discretionary items for optional reductions. Redirecting just 20% "
                f"of current discretionary spend ({format_currency_inr(savings_boost)}/mo) into "
                f"savings would increase your monthly contribution over {duration} years."
            ),
            metric_label="Discretionary % of Income",
            metric_value=f"{disc_pct:.1f}%",
        ))

    # ------------------------------------------------------------------
    # RULE 4 - Savings rate too low
    # ------------------------------------------------------------------
    if monthly_income > 0 and savings_rate < 10.0 and contrib > 0:
        target_15_contrib = monthly_income * 0.15
        recommendations.append(Recommendation(
            category="Savings",
            severity="info",
            title="Savings Rate Below 10% — Consider Gradual Increases",
            reason=(
                f"Your current savings rate is {savings_rate:.1f}% of monthly income "
                f"({format_currency_inr(contrib)}/mo). Financial planning literature generally "
                "suggests 15-20% as a healthy long-term target, though individual goals vary."
            ),
            action=(
                "Aim to incrementally increase your monthly contribution by small amounts "
                "(e.g., ₹500-₹1,000 every 6 months) as your income grows or expenses decrease. "
                f"A 15% savings rate would require {format_currency_inr(target_15_contrib)}/mo."
            ),
            metric_label="Current Savings Rate",
            metric_value=f"{savings_rate:.1f}%",
        ))

    # ------------------------------------------------------------------
    # RULE 5 & 6 - Goal feasibility (if target provided)
    # ------------------------------------------------------------------
    if target_amount and target_amount > 0:
        feasibility: TargetFeasibilityResult = calculate_target_feasibility(
            inputs, target_amount=target_amount
        )

        if feasibility.target_achieved:
            surplus_over = feasibility.surplus_or_shortfall
            recommendations.append(Recommendation(
                category="Goal",
                severity="positive",
                title="Savings Goal is Achievable Under Current Plan",
                reason=(
                    f"Your current plan projects {format_currency_inr(ending)} after {duration} years, "
                    f"which surpasses your target of {format_currency_inr(target_amount)} by "
                    f"{format_currency_inr(surplus_over)}."
                ),
                action=(
                    "Your plan is feasible as configured. If desired, you could reduce the monthly "
                    "contribution slightly and still achieve the goal, or set a more ambitious target."
                ),
                metric_label="Projected Surplus Over Goal",
                metric_value=format_currency_inr(surplus_over),
            ))
        else:
            shortfall = abs(feasibility.surplus_or_shortfall)
            if feasibility.required_monthly_contribution is not None:
                extra_needed = feasibility.required_monthly_contribution - contrib
                if feasibility.is_feasible_with_surplus:
                    recommendations.append(Recommendation(
                        category="Goal",
                        severity="warning",
                        title="Goal Requires a Higher Monthly Contribution",
                        reason=(
                            f"At the current contribution of {format_currency_inr(contrib)}/mo, "
                            f"the projected balance of {format_currency_inr(ending)} falls short of "
                            f"your target of {format_currency_inr(target_amount)} by "
                            f"{format_currency_inr(shortfall)}."
                        ),
                        action=(
                            f"Increase monthly contribution by {format_currency_inr(extra_needed)} "
                            f"to {format_currency_inr(feasibility.required_monthly_contribution)}/mo. "
                            f"This is affordable: your monthly surplus is "
                            f"{format_currency_inr(surplus)}, which covers the required increase."
                        ),
                        metric_label="Additional Contribution Needed",
                        metric_value=format_currency_inr(extra_needed),
                    ))
                else:
                    recommendations.append(Recommendation(
                        category="Goal",
                        severity="critical",
                        title="Goal Unachievable Within Current Budget and Duration",
                        reason=(
                            f"Reaching {format_currency_inr(target_amount)} in {duration} years "
                            f"requires {format_currency_inr(feasibility.required_monthly_contribution)}/mo "
                            f"— but your monthly surplus is only {format_currency_inr(max(0.0, surplus))}."
                        ),
                        action=(
                            f"Consider: (1) Extending duration beyond {duration} years to lower the "
                            "required monthly deposit, (2) Adjusting the target to match your current "
                            f"projected balance of {format_currency_inr(ending)}, or "
                            "(3) Finding ways to increase monthly income or reduce fixed expenses."
                        ),
                        metric_label="Required vs. Available Surplus",
                        metric_value=(
                            f"{format_currency_inr(feasibility.required_monthly_contribution)} "
                            f"needed vs {format_currency_inr(max(0.0, surplus))} available"
                        ),
                    ))

    # ------------------------------------------------------------------
    # RULE 7 - Inflation significantly erodes purchasing power
    # ------------------------------------------------------------------
    pwr_loss_pct = _pct(pwr_loss, ending)
    if inflation > 0 and pwr_loss_pct > 20.0 and ending > 0:
        real_return_note = (
            f"negative ({outputs.effective_real_return_rate:.1f}% real). "
            f"Explore instruments offering returns above {inflation:.1f}% p.a."
            if ret_rate < inflation else
            f"positive ({outputs.effective_real_return_rate:.1f}% real), "
            "which partially offsets inflation erosion."
        )
        recommendations.append(Recommendation(
            category="Inflation",
            severity="info",
            title="Inflation Will Significantly Erode Future Purchasing Power",
            reason=(
                f"At {inflation:.1f}% annual inflation, your nominal balance of "
                f"{format_currency_inr(ending)} will have real purchasing power of only "
                f"{format_currency_inr(real_val)} in today's money — a loss of "
                f"{format_currency_inr(pwr_loss)} ({pwr_loss_pct:.1f}%) over {duration} years."
            ),
            action=(
                f"Your current assumed return of {ret_rate:.1f}% yields a real return that is "
                + real_return_note
            ),
            metric_label="Purchasing Power Loss",
            metric_value=f"{format_currency_inr(pwr_loss)} ({pwr_loss_pct:.1f}%)",
        ))

    # ------------------------------------------------------------------
    # RULE 8 - Zero return assumption (informational)
    # ------------------------------------------------------------------
    if ret_rate == 0.0 and duration >= 3:
        recommendations.append(Recommendation(
            category="Growth",
            severity="info",
            title="Simulation Uses 0% Return (Pure Savings Model)",
            reason=(
                f"Your assumed return is 0%, so this projection ({format_currency_inr(ending)}) "
                "reflects only cumulative deposits with no compound growth. Over "
                f"{duration} years, even modest investment returns compound meaningfully."
            ),
            action=(
                "This is a conservative, educationally appropriate baseline. To model the effect "
                "of investing, experiment with the Return Rate slider (e.g., 6-8% for balanced "
                "instruments). Remember: higher assumed returns involve higher risk and are not "
                "guaranteed outcomes."
            ),
            metric_label="Assumed Return",
            metric_value="0.0% (no growth assumed)",
        ))

    # ------------------------------------------------------------------
    # RULE 9 - Duration extension opportunity
    # ------------------------------------------------------------------
    if duration < 10 and ending > 0 and contrib > 0:
        extended_inputs = SimulationInputs(
            monthly_income=inputs.monthly_income,
            essential_expenses=inputs.essential_expenses,
            discretionary_expenses=inputs.discretionary_expenses,
            current_savings=inputs.current_savings,
            monthly_contribution=contrib,
            duration_years=10,
            annual_inflation=inflation,
            annual_return=ret_rate,
            contribution_timing=inputs.contribution_timing,
        )
        extended_out = calculate_simulation(extended_inputs)
        gain = extended_out.projected_ending_balance - ending
        recommendations.append(Recommendation(
            category="Strategy",
            severity="info",
            title="Extending Time Horizon Would Amplify Compound Returns",
            reason=(
                f"Your simulation runs for {duration} year(s). Compounding becomes "
                "significantly more impactful over longer time horizons due to the "
                "exponential nature of compound interest on both principal and returns."
            ),
            action=(
                f"Projecting the same contributions over 10 years would result in "
                f"{format_currency_inr(extended_out.projected_ending_balance)}, which is "
                f"{format_currency_inr(gain)} more than your current {duration}-year projection. "
                "Consider whether a longer savings horizon is feasible for your goals."
            ),
            metric_label="Estimated 10-Year Gain",
            metric_value=format_currency_inr(gain),
        ))

    # ------------------------------------------------------------------
    # RULE 10 - Large initial savings as growth leverage
    # ------------------------------------------------------------------
    if inputs.current_savings > contrib * 24 and ret_rate > 0:
        r_m = (ret_rate / 100.0) / 12.0
        fv_lump = inputs.current_savings * math.pow(1 + r_m, duration * 12)
        share_pct = _pct(fv_lump, ending)
        recommendations.append(Recommendation(
            category="Strategy",
            severity="positive",
            title="Large Initial Balance is a Significant Growth Lever",
            reason=(
                f"Your initial savings of {format_currency_inr(inputs.current_savings)} is "
                f"substantial relative to your monthly contribution of {format_currency_inr(contrib)}/mo. "
                f"With an assumed return of {ret_rate:.1f}%, the lump-sum component alone will grow "
                f"to approximately {format_currency_inr(fv_lump)}, representing ~{share_pct:.0f}% "
                "of the final corpus."
            ),
            action=(
                "Your initial balance is doing significant compounding work. Ensure it is deployed "
                f"in instruments aligned with your {duration}-year time horizon and risk tolerance."
            ),
            metric_label="Initial Savings FV Contribution",
            metric_value=f"~{share_pct:.0f}% of ending corpus",
        ))

    # ------------------------------------------------------------------
    # RULE 11 - High savings rate praise
    # ------------------------------------------------------------------
    if monthly_income > 0 and savings_rate >= 25.0:
        recommendations.append(Recommendation(
            category="Savings",
            severity="positive",
            title="Excellent Savings Rate — Strong Financial Discipline",
            reason=(
                f"Your savings rate of {savings_rate:.1f}% significantly exceeds common "
                "benchmarks. This directly accelerates wealth accumulation through higher "
                "monthly deposits and a stronger compounding base."
            ),
            action=(
                "Maintain this rate consistently. Consider whether your savings are allocated "
                f"into instruments matching your risk tolerance and {duration}-year time horizon."
            ),
            metric_label="Savings Rate",
            metric_value=f"{savings_rate:.1f}%",
        ))

    # ------------------------------------------------------------------
    # Compile final report
    # ------------------------------------------------------------------
    issues = [r for r in recommendations if r.severity in ("critical", "warning")]
    positives = [r for r in recommendations if r.severity == "positive"]

    if not recommendations:
        summary = (
            f"Your financial plan appears well-configured with no critical issues detected. "
            f"Projected ending balance: {format_currency_inr(ending)} over {duration} years."
        )
    elif any(r.severity == "critical" for r in recommendations):
        summary = (
            "Critical issues detected in your financial plan. Addressing budget deficits or "
            "infeasible contributions should take priority before projecting outcomes."
        )
    else:
        summary = (
            f"{len(issues)} area(s) flagged for review. Projected balance: "
            f"{format_currency_inr(ending)} over {duration} years, "
            f"with {len(positives)} positive finding(s) identified."
        )

    return RecommendationReport(
        recommendations=recommendations,
        total_issues=len(issues),
        positive_findings=len(positives),
        summary=summary,
    )
