"""
Reusable UI Components for WhatIf AI.

Renders modern SaaS cards, banners, metric widgets, and callouts
using custom HTML/CSS adhering to the light-theme design system.
"""

import os
from typing import List, Optional
import streamlit as st

from src.calculations import (
    SimulationInputs,
    SimulationOutputs,
    format_currency_inr,
)


def load_custom_css():
    """Reads and injects assets/style.css into the active Streamlit app."""
    css_path = os.path.join(os.path.dirname(__file__), "..", "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def render_sidebar_brand():
    """Renders the top branding header inside the Streamlit sidebar."""
    html = """
    <div class="sidebar-brand-box">
        <div class="brand-title">
            <span style="display:inline-block; width:12px; height:12px; border-radius:3px; background:linear-gradient(135deg, #4f46e5, #7c3aed);"></span>
            WhatIf AI
        </div>
        <div class="brand-tagline">Explore possibilities. Make smarter decisions.</div>
        <div class="status-badge">
            <span class="status-dot"></span>
            Simulation Engine Ready
        </div>
    </div>
    """
    st.sidebar.markdown(html, unsafe_allow_html=True)


def render_page_header(breadcrumb: str, title: str, subtitle: str):
    """Renders the standard top navigation header for all application pages."""
    html = f"""
    <div style="margin-bottom: 1.5rem; padding-bottom: 0.75rem; border-bottom: 1px solid #e2e8f0;">
        <div style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #6366f1; margin-bottom: 0.35rem;">
            {breadcrumb}
        </div>
        <h1 style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 2rem; font-weight: 800; color: #0f172a; margin: 0 0 0.35rem 0; letter-spacing: -0.025em; line-height: 1.2;">
            {title}
        </h1>
        <div style="font-size: 0.98rem; color: #64748b; line-height: 1.5;">
            {subtitle}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_primary_metrics_grid(outputs: SimulationOutputs):
    """
    Renders the 4 core KPI metric cards:
    - Projected Ending Balance
    - Total Contributions
    - Estimated Compound Growth
    - Inflation-Adjusted Purchasing Power
    """
    growth_sign = "+" if outputs.estimated_growth > 0 else ""
    real_pct_loss = (
        (outputs.purchasing_power_loss / outputs.projected_ending_balance * 100.0)
        if outputs.projected_ending_balance > 0
        else 0.0
    )

    html = f"""
    <div class="metrics-grid">
        <div class="metric-card metric-card-primary">
            <div class="metric-card-label">
                <span>Projected Ending Balance</span>
                <span style="color:#4f46e5; font-size:1rem;">◈</span>
            </div>
            <div class="metric-card-value">{format_currency_inr(outputs.projected_ending_balance)}</div>
            <div class="metric-card-sub">Nominal balance after {outputs.inputs.duration_years} years ({outputs.total_months} months)</div>
        </div>
        <div class="metric-card metric-card-cyan">
            <div class="metric-card-label">
                <span>Total Contributions</span>
                <span style="color:#06b6d4; font-size:1rem;">▼</span>
            </div>
            <div class="metric-card-value">{format_currency_inr(outputs.total_contributed)}</div>
            <div class="metric-card-sub">{format_currency_inr(outputs.inputs.monthly_contribution)}/mo &bull; Initial: {format_currency_inr(outputs.inputs.current_savings)}</div>
        </div>
        <div class="metric-card metric-card-emerald">
            <div class="metric-card-label">
                <span>Estimated Growth</span>
                <span style="color:#10b981; font-size:1rem;">▲</span>
            </div>
            <div class="metric-card-value">{growth_sign}{format_currency_inr(outputs.estimated_growth)}</div>
            <div class="metric-card-sub">Assumed {outputs.inputs.annual_return:.1f}% annual return (compounded monthly)</div>
        </div>
        <div class="metric-card metric-card-amber">
            <div class="metric-card-label">
                <span>Real Purchasing Power</span>
                <span style="color:#f59e0b; font-size:1rem;">⏳</span>
            </div>
            <div class="metric-card-value">{format_currency_inr(outputs.inflation_adjusted_balance)}</div>
            <div class="metric-card-sub">{outputs.inputs.annual_inflation:.1f}% inflation drag (-{real_pct_loss:.1f}%)</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_assumptions_pills(inputs: SimulationInputs):
    """Renders a clean pill bar displaying active input parameters."""
    html = f"""
    <div class="pills-container">
        <div class="pill-item">Income: <strong>{format_currency_inr(inputs.monthly_income)}/mo</strong></div>
        <div class="pill-item">Essentials: <strong>{format_currency_inr(inputs.essential_expenses)}/mo</strong></div>
        <div class="pill-item">Discretionary: <strong>{format_currency_inr(inputs.discretionary_expenses)}/mo</strong></div>
        <div class="pill-item">Initial Balance: <strong>{format_currency_inr(inputs.current_savings)}</strong></div>
        <div class="pill-item">Target Contribution: <strong>{format_currency_inr(inputs.monthly_contribution)}/mo</strong></div>
        <div class="pill-item">Duration: <strong>{inputs.duration_years} Years</strong></div>
        <div class="pill-item">Inflation: <strong>{inputs.annual_inflation:.1f}%</strong></div>
        <div class="pill-item">Assumed Return: <strong>{inputs.annual_return:.1f}%</strong></div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_what_this_means(outputs: SimulationOutputs):
    """Renders a plain English 'What this means' narrative interpretation card."""
    surplus = outputs.monthly_surplus
    duration = outputs.inputs.duration_years
    contrib = outputs.inputs.monthly_contribution
    ending = outputs.projected_ending_balance
    real = outputs.inflation_adjusted_balance
    loss = outputs.purchasing_power_loss

    paragraphs = []

    # Surplus check
    if contrib > surplus and surplus >= 0:
        paragraphs.append(
            f"<b>Budget Warning:</b> Your chosen monthly contribution of <b>{format_currency_inr(contrib)}</b> exceeds your current monthly surplus of <b>{format_currency_inr(surplus)}</b>. You will need to reallocate discretionary spending or generate additional income to sustain this savings rate."
        )
    elif surplus < 0:
        paragraphs.append(
            f"<b>Deficit Alert:</b> Your total expenses exceed your income by <b>{format_currency_inr(abs(surplus))}</b> each month. Stabilizing essential and discretionary costs is necessary before executing this savings scenario."
        )
    else:
        paragraphs.append(
            f"<b>Feasibility Confirmed:</b> Your monthly contribution of <b>{format_currency_inr(contrib)}</b> fits comfortably within your monthly surplus of <b>{format_currency_inr(surplus)}</b> (leaving an unallocated buffer of {format_currency_inr(surplus - contrib)}/mo)."
        )

    # Growth and Inflation analysis
    if outputs.estimated_growth > 0:
        paragraphs.append(
            f"<b>Wealth Multiplication:</b> Over {duration} years, your cumulative deposits of <b>{format_currency_inr(outputs.total_contributed)}</b> combined with your starting savings will generate an estimated <b>{format_currency_inr(outputs.estimated_growth)}</b> in compound returns, expanding your nominal wealth to <b>{format_currency_inr(ending)}</b>."
        )
    else:
        paragraphs.append(
            f"<b>Pure Savings Model:</b> With zero investment return assumed, your ending balance of <b>{format_currency_inr(ending)}</b> is entirely composed of your initial capital plus your regular monthly savings ({format_currency_inr(outputs.total_contributed)})."
        )

    if outputs.inputs.annual_inflation > 0:
        paragraphs.append(
            f"<b>Inflation Impact:</b> Due to an assumed {outputs.inputs.annual_inflation:.1f}% annual inflation, prices will rise over the next {duration} years. Your future {format_currency_inr(ending)} will have the equivalent purchasing power of <b>{format_currency_inr(real)}</b> in today's money (an effective purchasing power erosion of {format_currency_inr(loss)})."
        )

    body_html = "<br><br>".join(paragraphs)
    html = f"""
    <div class="narrative-card">
        <div style="font-weight:700; font-size:1.05rem; color:#0f172a; margin-bottom:0.5rem; display:flex; align-items:center; gap:6px;">
            <span>💡</span> What this simulation means in plain English
        </div>
        <div>{body_html}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_feature_cards():
    """Renders the 3 core feature pillars on the Overview page."""
    html = """
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:1.25rem; margin:1.5rem 0 2rem 0;">
        <div class="feature-card">
            <div class="feature-icon-box">⚡</div>
            <div class="feature-title">Explore Scenarios</div>
            <div class="feature-desc">
                Adjust income, essential spending, discretionary habits, and contribution rates with live recalculations. Test short-term sprints or 30-year wealth trajectories.
            </div>
        </div>
        <div class="feature-card">
            <div class="feature-icon-box">⚖️</div>
            <div class="feature-title">Compare Outcomes</div>
            <div class="feature-desc">
                Place Conservative, Current, and Aggressive financial plans side-by-side. Inspect trajectory divergences, principal versus interest ratios, and baseline differences.
            </div>
        </div>
        <div class="feature-card">
            <div class="feature-icon-box">🎯</div>
            <div class="feature-title">Understand Trade-offs</div>
            <div class="feature-desc">
                Measure inflation erosion and conduct multi-parameter sensitivity analysis. Identify which lifestyle variables hold the greatest mathematical influence over your future.
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_how_it_works():
    """Renders the 3-step 'How it works' sequence on the Overview page."""
    html = """
    <div style="margin:2.5rem 0 1.5rem 0;">
        <h2 style="font-family:'Plus Jakarta Sans', sans-serif; font-size:1.45rem; font-weight:800; color:#0f172a; margin-bottom:0.5rem;">
            How WhatIf AI Works
        </h2>
        <div style="font-size:0.95rem; color:#64748b; margin-bottom:1.25rem;">
            A three-step scientific framework for conditional forward simulation.
        </div>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:1.25rem;">
            <div class="step-card">
                <div class="step-number">1</div>
                <div style="font-weight:700; font-size:1.05rem; color:#0f172a; margin-bottom:0.4rem;">Define Financial Constraints</div>
                <div style="font-size:0.9rem; color:#64748b; line-height:1.5;">
                    Input take-home income, mandatory living costs, discretionary lifestyle expenses, and current cash reserve balance.
                </div>
            </div>
            <div class="step-card">
                <div class="step-number">2</div>
                <div style="font-weight:700; font-size:1.05rem; color:#0f172a; margin-bottom:0.4rem;">Set Assumptions & Horizons</div>
                <div style="font-size:0.9rem; color:#64748b; line-height:1.5;">
                    Configure time horizon (1 to 30 years), expected annual returns, inflation expectations, and monthly savings allocation.
                </div>
            </div>
            <div class="step-card">
                <div class="step-number">3</div>
                <div style="font-weight:700; font-size:1.05rem; color:#0f172a; margin-bottom:0.4rem;">Evaluate Decisions & Sensitivity</div>
                <div style="font-size:0.9rem; color:#64748b; line-height:1.5;">
                    Review compound trajectories, inflation-discounted real wealth, tornado sensitivity charts, and export executive PDF summaries.
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
