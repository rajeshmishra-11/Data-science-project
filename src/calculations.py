"""
Core Mathematical and Financial Simulation Engine for WhatIf AI.

Provides mathematically verified functions for personal finance scenario modeling:
- Monthly compounding under ordinary annuity (end-of-period) or annuity-due (beginning)
- Inflation-adjusted purchasing power discounting
- Month-by-month and year-by-year trajectory schedule generation
- Analytical break-even and target feasibility calculations
- Input validation and surplus checking
"""

from dataclasses import dataclass
from typing import List, Optional
import math
import pandas as pd


@dataclass
class SimulationInputs:
    monthly_income: float = 40000.0
    essential_expenses: float = 18000.0
    discretionary_expenses: float = 8000.0
    current_savings: float = 50000.0
    monthly_contribution: float = 8000.0
    duration_years: int = 5
    annual_inflation: float = 5.0
    annual_return: float = 0.0
    contribution_timing: str = "end"  # "end" (ordinary annuity) or "beginning" (annuity due)


@dataclass
class ValidationResult:
    is_valid: bool
    warnings: List[str]
    errors: List[str]
    monthly_surplus: float
    total_expenses: float
    savings_rate: float
    expense_ratio: float


@dataclass
class SimulationOutputs:
    inputs: SimulationInputs
    total_expenses: float
    monthly_surplus: float
    savings_rate: float
    expense_ratio: float
    total_months: int
    total_contributed: float
    total_principal_invested: float
    projected_ending_balance: float
    estimated_growth: float
    inflation_adjusted_balance: float
    purchasing_power_loss: float
    effective_real_return_rate: float
    validation: ValidationResult


@dataclass
class TargetFeasibilityResult:
    target_amount: float
    current_projected_balance: float
    target_achieved: bool
    surplus_or_shortfall: float
    required_monthly_contribution: Optional[float]
    months_to_target_at_current_rate: Optional[int]
    years_to_target_at_current_rate: Optional[float]
    contribution_diff: Optional[float]
    is_feasible_with_surplus: bool
    note: str


def format_currency_inr(amount: float, precision: int = 0) -> str:
    """
    Format a numeric amount into Indian Rupee style (₹ XX,XX,XXX).
    Handles negative numbers gracefully.
    """
    if math.isnan(amount) or math.isinf(amount):
        return "₹0"
    
    is_negative = amount < 0
    abs_amount = abs(amount)
    
    # Split into integer and decimal part
    if precision > 0:
        base_str = f"{abs_amount:.{precision}f}"
        int_part, dec_part = base_str.split(".")
    else:
        int_part = str(int(round(abs_amount)))
        dec_part = ""
        
    # Indian numbering format grouping: last 3 digits, then groups of 2
    if len(int_part) <= 3:
        formatted_int = int_part
    else:
        last_three = int_part[-3:]
        remaining = int_part[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted_int = ",".join(groups) + "," + last_three
        
    res = f"₹{formatted_int}"
    if dec_part:
        res += f".{dec_part}"
    return f"-{res}" if is_negative else res


def validate_inputs(inputs: SimulationInputs) -> ValidationResult:
    """
    Validates user inputs, checks budgetary surplus, and identifies warnings and errors.
    """
    errors: List[str] = []
    warnings: List[str] = []

    if inputs.monthly_income < 0:
        errors.append("Monthly income cannot be negative.")
    if inputs.essential_expenses < 0:
        errors.append("Essential expenses cannot be negative.")
    if inputs.discretionary_expenses < 0:
        errors.append("Discretionary expenses cannot be negative.")
    if inputs.current_savings < 0:
        errors.append("Current savings balance cannot be negative.")
    if inputs.monthly_contribution < 0:
        errors.append("Monthly contribution cannot be negative.")
    if inputs.duration_years < 1 or inputs.duration_years > 50:
        errors.append("Simulation duration must be between 1 and 50 years.")
    if inputs.annual_inflation < 0:
        errors.append("Inflation rate cannot be negative.")
    if inputs.annual_return < -50 or inputs.annual_return > 100:
        errors.append("Annual return must be between -50% and 100%.")

    total_expenses = max(0.0, inputs.essential_expenses + inputs.discretionary_expenses)
    monthly_surplus = inputs.monthly_income - total_expenses
    
    savings_rate = (inputs.monthly_contribution / inputs.monthly_income * 100.0) if inputs.monthly_income > 0 else 0.0
    expense_ratio = (total_expenses / inputs.monthly_income * 100.0) if inputs.monthly_income > 0 else 0.0

    if total_expenses > inputs.monthly_income:
        warnings.append(
            f"Your total monthly expenses ({format_currency_inr(total_expenses)}) exceed your monthly income ({format_currency_inr(inputs.monthly_income)}) by {format_currency_inr(total_expenses - inputs.monthly_income)}."
        )

    if monthly_surplus >= 0 and inputs.monthly_contribution > monthly_surplus:
        warnings.append(
            f"Your monthly contribution target ({format_currency_inr(inputs.monthly_contribution)}) exceeds your available monthly surplus ({format_currency_inr(monthly_surplus)})."
        )
    elif monthly_surplus < 0 and inputs.monthly_contribution > 0:
        warnings.append(
            f"You have a monthly budget deficit of {format_currency_inr(abs(monthly_surplus))}. Saving {format_currency_inr(inputs.monthly_contribution)} will require reducing expenses or increasing income."
        )

    if savings_rate > 70.0 and inputs.monthly_income > 0:
        warnings.append(
            f"Your intended savings rate of {savings_rate:.1f}% is very ambitious. Ensure you have budgeted sufficiently for unexpected costs."
        )

    is_valid = len(errors) == 0

    return ValidationResult(
        is_valid=is_valid,
        warnings=warnings,
        errors=errors,
        monthly_surplus=monthly_surplus,
        total_expenses=total_expenses,
        savings_rate=savings_rate,
        expense_ratio=expense_ratio,
    )


def calculate_simulation(inputs: SimulationInputs) -> SimulationOutputs:
    """
    Performs deterministic multi-year compound savings & purchasing power calculations.
    
    Compounding logic:
    - Monthly compounding with rate r_m = (annual_return / 100) / 12
    - Lump sum future value: FV_lump = PV * (1 + r_m)^n
    - Annuity future value:
      * Ordinary annuity (end of month): FV_annuity = PMT * ((1 + r_m)^n - 1) / r_m
      * Annuity due (beginning of month): FV_annuity = PMT * ((1 + r_m)^n - 1) / r_m * (1 + r_m)
    - Zero return case: FV = PV + PMT * n
    - Real (inflation-adjusted) value: FV_real = FV / (1 + i)^t
    """
    validation = validate_inputs(inputs)
    total_months = int(inputs.duration_years * 12)
    total_contributed = inputs.monthly_contribution * total_months
    total_principal = inputs.current_savings + total_contributed

    r_annual = inputs.annual_return / 100.0
    r_monthly = r_annual / 12.0
    i_annual = inputs.annual_inflation / 100.0
    t_years = inputs.duration_years

    if abs(r_monthly) < 1e-9:
        # Zero return
        projected_ending_balance = total_principal
        estimated_growth = 0.0
    else:
        # Lump sum future value
        fv_lump = inputs.current_savings * math.pow(1.0 + r_monthly, total_months)
        # Annuity factor
        annuity_factor = (math.pow(1.0 + r_monthly, total_months) - 1.0) / r_monthly
        if inputs.contribution_timing == "beginning":
            annuity_factor *= (1.0 + r_monthly)
        fv_annuity = inputs.monthly_contribution * annuity_factor
        projected_ending_balance = fv_lump + fv_annuity
        estimated_growth = projected_ending_balance - total_principal

    # Prevent negative accumulation if extreme negative return
    projected_ending_balance = max(0.0, projected_ending_balance)
    estimated_growth = projected_ending_balance - total_principal

    # Inflation adjustment
    # Real value discounted by (1 + i)^t
    inflation_discount = math.pow(1.0 + i_annual, t_years) if i_annual >= -0.99 else 1.0
    inflation_adjusted_balance = projected_ending_balance / inflation_discount if inflation_discount > 0 else projected_ending_balance
    purchasing_power_loss = projected_ending_balance - inflation_adjusted_balance

    # Effective real return rate via Fisher equation approximation or exact real rate:
    # (1 + r_real) = (1 + r_nom) / (1 + i) => r_real = (r_nom - i) / (1 + i)
    if (1.0 + i_annual) > 0:
        effective_real_return_rate = ((1.0 + r_annual) / (1.0 + i_annual) - 1.0) * 100.0
    else:
        effective_real_return_rate = (r_annual - i_annual) * 100.0

    return SimulationOutputs(
        inputs=inputs,
        total_expenses=validation.total_expenses,
        monthly_surplus=validation.monthly_surplus,
        savings_rate=validation.savings_rate,
        expense_ratio=validation.expense_ratio,
        total_months=total_months,
        total_contributed=total_contributed,
        total_principal_invested=total_principal,
        projected_ending_balance=projected_ending_balance,
        estimated_growth=estimated_growth,
        inflation_adjusted_balance=inflation_adjusted_balance,
        purchasing_power_loss=purchasing_power_loss,
        effective_real_return_rate=effective_real_return_rate,
        validation=validation,
    )


def generate_monthly_schedule(inputs: SimulationInputs) -> pd.DataFrame:
    """
    Generates a granular month-by-month trajectory table.
    """
    total_months = int(inputs.duration_years * 12)
    r_monthly = (inputs.annual_return / 100.0) / 12.0
    i_annual = inputs.annual_inflation / 100.0

    records = []
    current_balance = inputs.current_savings
    cumulative_contributions = 0.0

    for m in range(1, total_months + 1):
        year_num = math.ceil(m / 12)
        month_in_year = ((m - 1) % 12) + 1
        opening_balance = current_balance

        contribution = inputs.monthly_contribution
        cumulative_contributions += contribution

        if inputs.contribution_timing == "beginning":
            balance_for_interest = opening_balance + contribution
            monthly_interest = balance_for_interest * r_monthly if r_monthly != 0 else 0.0
            closing_balance = balance_for_interest + monthly_interest
        else:
            # End of month
            monthly_interest = opening_balance * r_monthly if r_monthly != 0 else 0.0
            closing_balance = opening_balance + monthly_interest + contribution

        closing_balance = max(0.0, closing_balance)
        cumulative_principal = inputs.current_savings + cumulative_contributions
        cumulative_growth = closing_balance - cumulative_principal

        # Inflation discount at month m
        time_years = m / 12.0
        discount_factor = math.pow(1.0 + i_annual, time_years) if (1.0 + i_annual) > 0 else 1.0
        real_balance = closing_balance / discount_factor if discount_factor > 0 else closing_balance

        records.append({
            "Month": m,
            "Year": year_num,
            "Month_In_Year": month_in_year,
            "Opening_Balance": opening_balance,
            "Monthly_Contribution": contribution,
            "Monthly_Growth": monthly_interest,
            "Closing_Balance": closing_balance,
            "Cumulative_Contributions": cumulative_contributions,
            "Cumulative_Principal": cumulative_principal,
            "Cumulative_Growth": cumulative_growth,
            "Inflation_Discount_Factor": discount_factor,
            "Real_Balance": real_balance,
        })

        current_balance = closing_balance

    return pd.DataFrame(records)


def generate_yearly_schedule(inputs: SimulationInputs) -> pd.DataFrame:
    """
    Generates an annual aggregated schedule suitable for reports and display.
    """
    monthly_df = generate_monthly_schedule(inputs)
    if monthly_df.empty:
        return pd.DataFrame()

    yearly_rows = []
    for yr, group in monthly_df.groupby("Year"):
        first_row = group.iloc[0]
        last_row = group.iloc[-1]

        yearly_rows.append({
            "Year": int(yr),
            "Starting_Balance": first_row["Opening_Balance"],
            "Annual_Contributions": group["Monthly_Contribution"].sum(),
            "Annual_Growth": group["Monthly_Growth"].sum(),
            "Ending_Balance": last_row["Closing_Balance"],
            "Cumulative_Contributed": last_row["Cumulative_Contributions"],
            "Total_Principal": last_row["Cumulative_Principal"],
            "Total_Growth": last_row["Cumulative_Growth"],
            "Real_Ending_Balance": last_row["Real_Balance"],
            "Purchasing_Power_Loss": last_row["Closing_Balance"] - last_row["Real_Balance"],
        })

    return pd.DataFrame(yearly_rows)


def calculate_target_feasibility(inputs: SimulationInputs, target_amount: float) -> TargetFeasibilityResult:
    """
    Evaluates feasibility of reaching a user-defined target savings amount.
    Calculates:
    - Required monthly contribution to hit target at specified duration.
    - Time required (months/years) at current monthly contribution.
    - Surplus feasibility check.
    """
    validation = validate_inputs(inputs)
    outputs = calculate_simulation(inputs)
    projected = outputs.projected_ending_balance
    target = max(0.0, float(target_amount))

    surplus_or_shortfall = projected - target
    target_achieved = surplus_or_shortfall >= 0

    total_months = int(inputs.duration_years * 12)
    r_monthly = (inputs.annual_return / 100.0) / 12.0

    # 1. Calculate required monthly contribution to reach target
    required_contribution: Optional[float] = None
    if total_months > 0:
        if abs(r_monthly) < 1e-9:
            # target = current_savings + req_pmt * n
            net_needed = target - inputs.current_savings
            required_contribution = max(0.0, net_needed / total_months)
        else:
            # target = current_savings * (1+r)^n + req_pmt * factor
            fv_initial = inputs.current_savings * math.pow(1.0 + r_monthly, total_months)
            net_needed = target - fv_initial
            factor = (math.pow(1.0 + r_monthly, total_months) - 1.0) / r_monthly
            if inputs.contribution_timing == "beginning":
                factor *= (1.0 + r_monthly)
            
            if factor > 0:
                required_contribution = max(0.0, net_needed / factor)
            else:
                required_contribution = None

    # 2. Calculate time in months to reach target with CURRENT contribution
    months_to_target: Optional[int] = None
    years_to_target: Optional[float] = None

    if target <= inputs.current_savings:
        months_to_target = 0
        years_to_target = 0.0
    elif inputs.monthly_contribution <= 0 and inputs.annual_return <= 0:
        months_to_target = None
        years_to_target = None
    else:
        if abs(r_monthly) < 1e-9:
            if inputs.monthly_contribution > 0:
                needed = target - inputs.current_savings
                m = math.ceil(needed / inputs.monthly_contribution)
                months_to_target = m
                years_to_target = round(m / 12.0, 1)
        else:
            # Analytic solution:
            # target = P0 * (1+r)^n + PMT * ((1+r)^n - 1) / r
            # target * r = P0 * r * (1+r)^n + PMT * (1+r)^n - PMT
            # target * r + PMT = (1+r)^n * (P0 * r + PMT)
            # (1+r)^n = (target * r + PMT) / (P0 * r + PMT)
            pmt = inputs.monthly_contribution
            if inputs.contribution_timing == "beginning":
                pmt = pmt * (1.0 + r_monthly)

            numerator = target * r_monthly + pmt
            denominator = inputs.current_savings * r_monthly + pmt

            if numerator > 0 and denominator > 0 and (numerator / denominator) > 1.0:
                try:
                    n_float = math.log(numerator / denominator) / math.log(1.0 + r_monthly)
                    months_to_target = math.ceil(n_float)
                    years_to_target = round(months_to_target / 12.0, 1)
                except (ValueError, ZeroDivisionError):
                    months_to_target = None
                    years_to_target = None

    # Check whether required contribution fits within monthly surplus
    is_feasible_with_surplus = True
    if required_contribution is not None:
        if validation.monthly_surplus < required_contribution:
            is_feasible_with_surplus = False

    contribution_diff = (required_contribution - inputs.monthly_contribution) if required_contribution is not None else None

    # Generate note
    if target_achieved:
        note = (
            f"Goal on track: Projected to reach {format_currency_inr(projected)} in {inputs.duration_years} years, "
            f"surpassing your target of {format_currency_inr(target)} by {format_currency_inr(surplus_or_shortfall)}."
        )
    else:
        if required_contribution is not None:
            extra = required_contribution - inputs.monthly_contribution
            if is_feasible_with_surplus:
                note = (
                    f"Target shortfall of {format_currency_inr(abs(surplus_or_shortfall))}. "
                    f"To achieve {format_currency_inr(target)} in {inputs.duration_years} years, "
                    f"increase monthly contribution by {format_currency_inr(extra)} (to {format_currency_inr(required_contribution)}/mo), "
                    f"which is fully affordable within your monthly surplus of {format_currency_inr(validation.monthly_surplus)}."
                )
            else:
                note = (
                    f"Target shortfall of {format_currency_inr(abs(surplus_or_shortfall))}. "
                    f"Achieving this target in {inputs.duration_years} years requires {format_currency_inr(required_contribution)}/mo "
                    f"(an increase of {format_currency_inr(extra)}/mo). This exceeds your current monthly surplus of "
                    f"{format_currency_inr(validation.monthly_surplus)}. Extending duration or lowering expenses is recommended."
                )
        else:
            note = f"Target is currently unattainable under the selected parameters without increasing contributions."

    return TargetFeasibilityResult(
        target_amount=target,
        current_projected_balance=projected,
        target_achieved=target_achieved,
        surplus_or_shortfall=surplus_or_shortfall,
        required_monthly_contribution=required_contribution,
        months_to_target_at_current_rate=months_to_target,
        years_to_target_at_current_rate=years_to_target,
        contribution_diff=contribution_diff,
        is_feasible_with_surplus=is_feasible_with_surplus,
        note=note,
    )
