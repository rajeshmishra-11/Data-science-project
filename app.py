"""
WhatIf AI - Interactive Decision Intelligence & Future Scenario Simulator
Main Streamlit Application.
"""

import io
from datetime import datetime
import streamlit as st
import pandas as pd

from src.calculations import (
    SimulationInputs,
    SimulationOutputs,
    calculate_simulation,
    calculate_target_feasibility,
    generate_yearly_schedule,
    generate_monthly_schedule,
    format_currency_inr,
)
from src.scenarios import (
    Scenario,
    get_default_preset_scenarios,
    compare_scenarios,
    build_multi_scenario_trajectory_dataframe,
)
from src.sensitivity import (
    compute_tornado_analysis,
    compute_1d_sweep_contribution,
    compute_1d_sweep_returns,
)
from src.visualizations import (
    plot_wealth_accumulation_trajectory,
    plot_nominal_vs_real_purchasing_power,
    plot_asset_composition_breakdown,
    plot_scenario_comparison_trajectories,
    plot_tornado_sensitivity_chart,
    plot_1d_sweep_curve,
    plot_uncertainty_scenario_trajectories,
    plot_uncertainty_summary_bars,
    plot_experiment_response_curve,
    plot_experiment_grouped_bars,
    PALETTE,
)

try:
    from src.visualizations import render_plotly_chart, PLOTLY_CONFIG
except ImportError:
    PLOTLY_CONFIG = {"responsive": True, "displayModeBar": "hover", "displaylogo": False}
    def render_plotly_chart(fig, key=None):
        try:
            st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG, key=key)
        except TypeError:
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG, key=key)
from src.report_generator import generate_pdf_report, generate_csv_export
from src.ui_components import (
    load_custom_css,
    render_sidebar_brand,
    render_page_header,
    render_primary_metrics_grid,
    render_assumptions_pills,
    render_what_this_means,
    render_feature_cards,
    render_how_it_works,
)
from src.recommendation_engine import generate_recommendations, Recommendation
from src.uncertainty_analysis import (
    get_default_scenario_configs,
    compute_future_scenario_explorer,
    explain_scenario_spread,
    UncertaintyScenarioConfig,
)
from src.experiment_lab import (
    run_experiment_a,
    run_experiment_b,
    run_experiment_c,
    run_experiment_d,
    export_experiment_results_csv,
    export_experiment_summary_report,
)

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="WhatIf AI — Scenario Simulator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom SaaS CSS design system
load_custom_css()

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "Overview"

if "inputs" not in st.session_state:
    st.session_state.inputs = SimulationInputs()

if "target_goal" not in st.session_state:
    st.session_state.target_goal = 1000000.0  # ₹10 Lakhs

if "scenarios" not in st.session_state:
    st.session_state.scenarios = get_default_preset_scenarios(st.session_state.inputs)

if "baseline_id" not in st.session_state:
    st.session_state.baseline_id = "current_plan"

if "simulation_history" not in st.session_state:
    st.session_state.simulation_history = []


def navigate_to(page_name: str):
    """Callback to switch application pages cleanly."""
    st.session_state.current_page = page_name


# -----------------------------------------------------------------------------
# Sidebar Navigation
# -----------------------------------------------------------------------------
with st.sidebar:
    render_sidebar_brand()

    pages = [
        "Overview",
        "Finance Simulator",
        "Future Scenario Explorer",
        "Recommendation Engine",
        "Scenario Comparison",
        "Data Science Experiment Lab",
        "Data Science & Sensitivity",
        "Insights & Methodology",
        "About the Project",
    ]

    # Map icons for sidebar display
    page_icons = {
        "Overview": "🏠",
        "Finance Simulator": "💼",
        "Future Scenario Explorer": "🔮",
        "Recommendation Engine": "💡",
        "Scenario Comparison": "⚖️",
        "Data Science Experiment Lab": "🧪",
        "Data Science & Sensitivity": "🔬",
        "Insights & Methodology": "📖",
        "About the Project": "🎓",
    }

    selected_page = st.radio(
        "Navigation Menu",
        options=pages,
        index=pages.index(st.session_state.current_page) if st.session_state.current_page in pages else 0,
        format_func=lambda x: f"{page_icons.get(x, '•')}  {x}",
        label_visibility="collapsed",
    )
    st.session_state.current_page = selected_page

    st.markdown("---")
    st.caption("Active Session Quick Stats")
    active_sc_count = len(st.session_state.scenarios)
    active_out = calculate_simulation(st.session_state.inputs)
    st.markdown(
        f"""
        <div style="font-size:0.85rem; color:#475569; line-height:1.6;">
            &bull; <b>Active Corpus:</b> {format_currency_inr(active_out.projected_ending_balance)}<br>
            &bull; <b>Monthly Target:</b> {format_currency_inr(st.session_state.inputs.monthly_contribution)}<br>
            &bull; <b>Saved Scenarios:</b> {active_sc_count} active
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("↺ Reset All to Defaults", use_container_width=True):
        st.session_state.inputs = SimulationInputs()
        st.session_state.scenarios = get_default_preset_scenarios(st.session_state.inputs)
        st.session_state.baseline_id = "current_plan"
        st.session_state.target_goal = 1000000.0
        st.rerun()


# -----------------------------------------------------------------------------
# PAGE 1: OVERVIEW
# -----------------------------------------------------------------------------
if st.session_state.current_page == "Overview":
    render_page_header(
        breadcrumb="Decision Intelligence Platform",
        title="What if your next decision was easier to understand?",
        subtitle="Explore different financial scenarios, compare possible futures, and understand how small changes can affect your long-term savings.",
    )

    # Hero Banner with CTA
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-badge">⚡ Real-Time Scenario Engine</div>
            <div class="hero-heading">Anticipate Outcomes Before You Commit.</div>
            <div class="hero-subtitle">
                Traditional budgets record where money went. WhatIf AI simulates where your choices will take you.
                Adjust income, essential spending, discretionary habits, and return assumptions to uncover long-term trade-offs.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        if st.button("🚀 Start Exploring Simulator", type="primary", use_container_width=True):
            navigate_to("Finance Simulator")
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Large Scenario Preview Card backed by real calculations
    st.markdown(
        """
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:16px; padding:1.5rem; margin-bottom:1.5rem; box-shadow:0 4px 6px -1px rgba(15,23,42,0.05);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
                <div>
                    <span style="font-size:0.8rem; font-weight:700; color:#4f46e5; text-transform:uppercase; letter-spacing:0.05em;">Interactive Model Preview</span>
                    <h3 style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.3rem; font-weight:700; margin:0.2rem 0; color:#0f172a;">
                        Baseline Scenario Trajectory (5-Year Growth Horizon)
                    </h3>
                </div>
                <div style="background:#eef2ff; color:#4338ca; padding:4px 12px; border-radius:9999px; font-size:0.8rem; font-weight:600;">
                    Live Calculation
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    preview_inputs = st.session_state.inputs
    preview_monthly = generate_monthly_schedule(preview_inputs)
    fig_preview = plot_wealth_accumulation_trajectory(preview_monthly, target_amount=st.session_state.target_goal)
    fig_preview.update_layout(height=420)
    render_plotly_chart(fig_preview, key="chart_preview")

    # 3 Feature Pillars
    render_feature_cards()

    # How it Works Section
    render_how_it_works()

    # Recent In-Session Simulations Section
    st.markdown(
        """
        <h2 style="font-family:'Plus Jakarta Sans', sans-serif; font-size:1.4rem; font-weight:800; color:#0f172a; margin-top:2rem; margin-bottom:0.35rem;">
            Recent In-Session Simulations
        </h2>
        <div style="font-size:0.92rem; color:#64748b; margin-bottom:1rem;">
            Simulations performed during your current active session.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.simulation_history:
        history_df = pd.DataFrame(st.session_state.simulation_history)
        st.dataframe(history_df, use_container_width=True, hide_index=True)
    else:
        st.markdown(
            """
            <div style="background:#ffffff; border:1px dashed #cbd5e1; border-radius:12px; padding:2rem; text-align:center; color:#64748b; margin-bottom:2rem;">
                <div style="font-size:1.8rem; margin-bottom:0.4rem;">📊</div>
                <div style="font-weight:600; color:#0f172a; font-size:1rem; margin-bottom:0.25rem;">No simulations executed yet in this session</div>
                <div style="font-size:0.88rem; max-width:480px; margin:0 auto 1rem auto;">
                    Open the Finance Simulator, adjust financial parameters, and click "Run Simulation" or save a scenario to build your comparative session log.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# -----------------------------------------------------------------------------
# PAGE 2: FINANCE SIMULATOR (THE CORE FEATURE)
# -----------------------------------------------------------------------------
elif st.session_state.current_page == "Finance Simulator":
    render_page_header(
        breadcrumb="Core Simulation Engine",
        title="Personal Finance & Savings Simulator",
        subtitle="Model conditional futures by adjusting income, essential living costs, discretionary habits, and return rates.",
    )

    # Main Grid Layout: Left Column Inputs (4 cols), Right Column Results (8 cols)
    col_inputs, col_results = st.columns([4, 8], gap="large")

    with col_inputs:
        st.markdown(
            """
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:14px; padding:1.25rem; box-shadow:0 1px 3px rgba(15,23,42,0.05); margin-bottom:1rem;">
                <h3 style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.15rem; font-weight:700; margin:0 0 0.25rem 0; color:#0f172a;">
                    Simulation Parameters
                </h3>
                <div style="font-size:0.82rem; color:#64748b; margin-bottom:1rem;">
                    Configure monthly cash flow, savings targets, and macroeconomic assumptions.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("💵 Monthly Cash Flow", expanded=True):
            monthly_income = st.number_input(
                "Take-Home Income (₹/month)",
                min_value=0.0,
                max_value=10000000.0,
                value=float(st.session_state.inputs.monthly_income),
                step=5000.0,
                help="Net monthly income after taxes and standard payroll deductions.",
            )

            essential_expenses = st.number_input(
                "Essential Expenses (₹/month)",
                min_value=0.0,
                max_value=10000000.0,
                value=float(st.session_state.inputs.essential_expenses),
                step=2000.0,
                help="Fixed necessities: rent/EMI, utilities, groceries, insurance, loan minimums.",
            )

            discretionary_expenses = st.number_input(
                "Discretionary Expenses (₹/month)",
                min_value=0.0,
                max_value=10000000.0,
                value=float(st.session_state.inputs.discretionary_expenses),
                step=1000.0,
                help="Flexible lifestyle spending: dining out, entertainment, subscriptions, shopping.",
            )

            current_savings = st.number_input(
                "Current Savings Balance (₹)",
                min_value=0.0,
                max_value=100000000.0,
                value=float(st.session_state.inputs.current_savings),
                step=10000.0,
                help="Existing cash reserves, emergency funds, or liquid investments already accumulated.",
            )

        with st.expander("🎯 Savings & Horizon Target", expanded=True):
            monthly_contribution = st.number_input(
                "Monthly Savings Contribution (₹/month)",
                min_value=0.0,
                max_value=10000000.0,
                value=float(st.session_state.inputs.monthly_contribution),
                step=1000.0,
                help="Target amount you intend to deposit and save each month.",
            )

            duration_years = st.slider(
                "Simulation Duration (Years)",
                min_value=1,
                max_value=30,
                value=int(st.session_state.inputs.duration_years),
                step=1,
                help="Total time horizon to project forward.",
            )

            target_goal = st.number_input(
                "Target Savings Goal (₹ Benchmark)",
                min_value=0.0,
                max_value=1000000000.0,
                value=float(st.session_state.target_goal),
                step=50000.0,
                help="Benchmark financial goal (e.g. ₹10 Lakhs emergency fund or home down-payment).",
            )
            st.session_state.target_goal = target_goal

        with st.expander("📈 Economic Assumptions", expanded=True):
            annual_inflation = st.slider(
                "Annual Inflation Assumption (%)",
                min_value=0.0,
                max_value=15.0,
                value=float(st.session_state.inputs.annual_inflation),
                step=0.5,
                help="Assumed long-term inflation rate (RBI target range is typically 4% to 6%).",
            )

            annual_return = st.slider(
                "Assumed Annual Return Rate (%)",
                min_value=0.0,
                max_value=20.0,
                value=float(st.session_state.inputs.annual_return),
                step=0.5,
                help="0% represents simple bank deposit. 6-8% represents conservative debt/hybrid. 10-14% represents equity funds.",
            )

            timing_choice = st.selectbox(
                "Contribution Timing",
                options=["end", "beginning"],
                index=0 if st.session_state.inputs.contribution_timing == "end" else 1,
                format_func=lambda x: "End of Month (Ordinary Annuity)" if x == "end" else "Beginning of Month (Annuity Due)",
            )

        # Update active inputs object
        active_inputs = SimulationInputs(
            monthly_income=monthly_income,
            essential_expenses=essential_expenses,
            discretionary_expenses=discretionary_expenses,
            current_savings=current_savings,
            monthly_contribution=monthly_contribution,
            duration_years=duration_years,
            annual_inflation=annual_inflation,
            annual_return=annual_return,
            contribution_timing=timing_choice,
        )
        st.session_state.inputs = active_inputs

        # Action Buttons
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            run_clicked = st.button("⚡ Run Simulation", type="primary", use_container_width=True)
        with col_act2:
            if st.button("↺ Reset Defaults", use_container_width=True):
                st.session_state.inputs = SimulationInputs()
                st.session_state.target_goal = 1000000.0
                st.rerun()

        # Save Scenario Control
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("💾 Save as Scenario for Comparison", expanded=False):
            save_name = st.text_input("Scenario Name", value=f"Plan {len(st.session_state.scenarios)+1}")
            save_desc = st.text_area("Scenario Notes", value=f"Duration: {duration_years}y, Contrib: {format_currency_inr(monthly_contribution)}, Return: {annual_return}%")
            if st.button("Save Scenario to Session", use_container_width=True):
                new_id = f"custom_{datetime.now().strftime('%M%S')}"
                new_scenario = Scenario(
                    id=new_id,
                    name=save_name,
                    description=save_desc,
                    inputs=active_inputs,
                    color="#4f46e5",
                )
                new_scenario.evaluate()
                st.session_state.scenarios.append(new_scenario)
                st.success(f"Scenario '{save_name}' saved! Compare it in the Scenario Comparison tab.")

    with col_results:
        # Run Calculation
        outputs = calculate_simulation(active_inputs)

        # Log to simulation history if run clicked
        if run_clicked:
            st.session_state.simulation_history.insert(0, {
                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                "Monthly Contribution": format_currency_inr(outputs.inputs.monthly_contribution),
                "Duration": f"{outputs.inputs.duration_years} Years",
                "Projected Balance": format_currency_inr(outputs.projected_ending_balance),
                "Real Purchasing Power": format_currency_inr(outputs.inflation_adjusted_balance),
                "Assumed Return": f"{outputs.inputs.annual_return:.1f}%",
            })
            if len(st.session_state.simulation_history) > 10:
                st.session_state.simulation_history.pop()

        # Display Validation Warnings if any
        if outputs.validation.warnings:
            for w in outputs.validation.warnings:
                st.markdown(
                    f"""
                    <div class="narrative-card narrative-card-warning" style="margin:0 0 1rem 0;">
                        ⚠️ <b>Attention:</b> {w}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Primary 4 KPI Metric Cards
        render_primary_metrics_grid(outputs)

        # Plain English "What this means" narrative
        render_what_this_means(outputs)

        # Active Assumptions Summary Pill Bar
        render_assumptions_pills(active_inputs)

        # Visualizations Tabs
        tab_trajectory, tab_real, tab_composition, tab_target = st.tabs([
            "📈 Wealth Trajectory",
            "⏳ Real Purchasing Power",
            "🍰 Asset Composition",
            "🎯 Goal Feasibility",
        ])

        monthly_df = generate_monthly_schedule(active_inputs)

        with tab_trajectory:
            fig_traj = plot_wealth_accumulation_trajectory(monthly_df, target_amount=target_goal)
            render_plotly_chart(fig_traj, key="chart_trajectory")

        with tab_real:
            fig_real = plot_nominal_vs_real_purchasing_power(monthly_df, annual_inflation=active_inputs.annual_inflation)
            render_plotly_chart(fig_real, key="chart_real")

        with tab_composition:
            fig_comp = plot_asset_composition_breakdown(outputs)
            render_plotly_chart(fig_comp, key="chart_composition")

        with tab_target:
            feasibility = calculate_target_feasibility(active_inputs, target_amount=target_goal)
            
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                status_color = "#10b981" if feasibility.target_achieved else "#f59e0b"
                status_text = "Goal Achieved" if feasibility.target_achieved else "Shortfall"
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-card-label">Target Goal Status</div>
                        <div class="metric-card-value" style="color:{status_color};">{status_text}</div>
                        <div class="metric-card-sub">Target: {format_currency_inr(target_goal)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_f2:
                req_val_str = format_currency_inr(feasibility.required_monthly_contribution) if feasibility.required_monthly_contribution is not None else "N/A"
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-card-label">Required Contribution</div>
                        <div class="metric-card-value">{req_val_str}</div>
                        <div class="metric-card-sub">To hit target in {active_inputs.duration_years} years</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_f3:
                time_str = f"{feasibility.years_to_target_at_current_rate:.1f} Years" if feasibility.years_to_target_at_current_rate is not None else "Unreachable"
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-card-label">Est. Time to Goal</div>
                        <div class="metric-card-value">{time_str}</div>
                        <div class="metric-card-sub">At current {format_currency_inr(active_inputs.monthly_contribution)}/mo deposit</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown(
                f"""
                <div class="narrative-card" style="margin-top:1rem;">
                    🎯 <b>Break-Even Analysis:</b> {feasibility.note}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Annual Schedule Table (Expandable)
        with st.expander("📋 Detailed Year-by-Year Schedule Table", expanded=False):
            yearly_df = generate_yearly_schedule(active_inputs)
            # Format currency columns for clean presentation
            disp_df = yearly_df.copy()
            for col in ["Starting_Balance", "Annual_Contributions", "Annual_Growth", "Ending_Balance", "Cumulative_Contributed", "Real_Ending_Balance", "Purchasing_Power_Loss"]:
                disp_df[col] = disp_df[col].apply(lambda x: format_currency_inr(x))
            st.dataframe(disp_df, use_container_width=True, hide_index=True)

        # Download Report Section
        st.markdown("<br>", unsafe_allow_html=True)
        col_down1, col_down2 = st.columns(2)

        with col_down1:
            # Generate ReportLab PDF
            pdf_buffer = generate_pdf_report(
                scenario_name="Active Plan",
                inputs=active_inputs,
                outputs=outputs,
                comparison_scenarios=st.session_state.scenarios,
            )
            st.download_button(
                label="📄 Download Executive PDF Report",
                data=pdf_buffer,
                file_name=f"WhatIf_AI_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        with col_down2:
            csv_data = generate_csv_export(active_inputs)
            st.download_button(
                label="📊 Export Annual Schedule (CSV)",
                data=csv_data,
                file_name=f"WhatIf_AI_Schedule_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )


# -----------------------------------------------------------------------------
# PAGE 3: FUTURE SCENARIO EXPLORER (MODULE 1)
# -----------------------------------------------------------------------------
elif st.session_state.current_page == "Future Scenario Explorer":
    render_page_header(
        breadcrumb="Uncertainty & Risk Analysis",
        title="Future Scenario Explorer",
        subtitle="Compare Optimistic, Moderate, and Pessimistic financial projections under different assumptions. These are hypothetical scenarios — not guaranteed financial outcomes.",
    )

    st.markdown(
        """
        <div style="background:#fffbeb; border:1px solid #fde68a; border-radius:12px; padding:1rem; margin-bottom:1.5rem;">
            <b>⚠️ Educational Disclaimer:</b> All projections here are hypothetical mathematical simulations
            based on user-specified assumptions. Investment returns are not guaranteed. Inflation, returns,
            and contribution amounts may differ significantly from actual future conditions. This tool
            is designed for decision-support and educational exploration only.
        </div>
        """,
        unsafe_allow_html=True,
    )

    base_inputs = st.session_state.inputs
    default_configs = get_default_scenario_configs(
        base_contribution=base_inputs.monthly_contribution,
        base_inflation=base_inputs.annual_inflation,
        base_return=base_inputs.annual_return,
        base_duration=base_inputs.duration_years,
    )

    # ---- Configure Scenarios ----
    st.markdown(
        """<h3 style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.2rem; font-weight:700; color:#0f172a; margin-top:0.5rem; margin-bottom:0.75rem;">
            ⚙️ Configure Scenario Assumptions
        </h3>""",
        unsafe_allow_html=True,
    )

    col_opt, col_mod, col_pess = st.columns(3, gap="medium")

    with col_opt:
        st.markdown("<div style='background:#ecfdf5; border:1px solid #6ee7b7; border-radius:10px; padding:0.75rem; margin-bottom:0.75rem;'><b style='color:#059669;'>🌟 Optimistic Scenario</b></div>", unsafe_allow_html=True)
        opt_contrib = st.number_input("Monthly Contribution (₹)", min_value=0.0, max_value=500000.0,
            value=float(default_configs["optimistic"].monthly_contribution), step=500.0, key="opt_contrib")
        opt_return = st.slider("Annual Return (%)", 0.0, 20.0,
            value=float(default_configs["optimistic"].annual_return), step=0.5, key="opt_return")
        opt_inflation = st.slider("Annual Inflation (%)", 0.0, 15.0,
            value=float(default_configs["optimistic"].annual_inflation), step=0.5, key="opt_inflation")
        opt_duration = st.slider("Duration (Years)", 1, 30,
            value=int(default_configs["optimistic"].duration_years), step=1, key="opt_duration")

    with col_mod:
        st.markdown("<div style='background:#eef2ff; border:1px solid #a5b4fc; border-radius:10px; padding:0.75rem; margin-bottom:0.75rem;'><b style='color:#4338ca;'>📊 Moderate Scenario</b></div>", unsafe_allow_html=True)
        mod_contrib = st.number_input("Monthly Contribution (₹)", min_value=0.0, max_value=500000.0,
            value=float(default_configs["moderate"].monthly_contribution), step=500.0, key="mod_contrib")
        mod_return = st.slider("Annual Return (%)", 0.0, 20.0,
            value=float(default_configs["moderate"].annual_return), step=0.5, key="mod_return")
        mod_inflation = st.slider("Annual Inflation (%)", 0.0, 15.0,
            value=float(default_configs["moderate"].annual_inflation), step=0.5, key="mod_inflation")
        mod_duration = st.slider("Duration (Years)", 1, 30,
            value=int(default_configs["moderate"].duration_years), step=1, key="mod_duration")

    with col_pess:
        st.markdown("<div style='background:#fff1f2; border:1px solid #fda4af; border-radius:10px; padding:0.75rem; margin-bottom:0.75rem;'><b style='color:#be123c;'>⛈️ Pessimistic Scenario</b></div>", unsafe_allow_html=True)
        pess_contrib = st.number_input("Monthly Contribution (₹)", min_value=0.0, max_value=500000.0,
            value=float(default_configs["pessimistic"].monthly_contribution), step=500.0, key="pess_contrib")
        pess_return = st.slider("Annual Return (%)", 0.0, 20.0,
            value=float(default_configs["pessimistic"].annual_return), step=0.5, key="pess_return")
        pess_inflation = st.slider("Annual Inflation (%)", 0.0, 15.0,
            value=float(default_configs["pessimistic"].annual_inflation), step=0.5, key="pess_inflation")
        pess_duration = st.slider("Duration (Years)", 1, 30,
            value=int(default_configs["pessimistic"].duration_years), step=1, key="pess_duration")

    # Build configs and run computation
    opt_cfg = UncertaintyScenarioConfig(
        monthly_contribution=opt_contrib, annual_inflation=opt_inflation,
        annual_return=opt_return, duration_years=int(opt_duration),
        label="Optimistic", color="#10b981", description="User-configured optimistic scenario.",
    )
    mod_cfg = UncertaintyScenarioConfig(
        monthly_contribution=mod_contrib, annual_inflation=mod_inflation,
        annual_return=mod_return, duration_years=int(mod_duration),
        label="Moderate", color="#4f46e5", description="User-configured moderate scenario.",
    )
    pess_cfg = UncertaintyScenarioConfig(
        monthly_contribution=pess_contrib, annual_inflation=pess_inflation,
        annual_return=pess_return, duration_years=int(pess_duration),
        label="Pessimistic", color="#f43f5e", description="User-configured pessimistic scenario.",
    )

    explorer_result = compute_future_scenario_explorer(
        optimistic_config=opt_cfg,
        moderate_config=mod_cfg,
        pessimistic_config=pess_cfg,
        initial_savings=base_inputs.current_savings,
        contribution_timing=base_inputs.contribution_timing,
    )

    # ---- Results Summary Cards ----
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """<h3 style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.2rem; font-weight:700; color:#0f172a; margin-bottom:0.75rem;">
            📊 Projected Outcomes
        </h3>""",
        unsafe_allow_html=True,
    )

    rc1, rc2, rc3 = st.columns(3, gap="medium")
    for col, result, label, bg, bd in [
        (rc1, explorer_result.pessimistic, "Pessimistic", "#fff1f2", "#f43f5e"),
        (rc2, explorer_result.moderate, "Moderate", "#eef2ff", "#4f46e5"),
        (rc3, explorer_result.optimistic, "Optimistic", "#ecfdf5", "#10b981"),
    ]:
        with col:
            st.markdown(
                f"""
                <div style="background:{bg}; border:2px solid {bd}; border-radius:14px; padding:1.25rem;">
                    <div style="font-weight:700; font-size:0.85rem; color:{bd}; margin-bottom:0.5rem; text-transform:uppercase;">{label}</div>
                    <div style="font-size:1.5rem; font-weight:800; color:#0f172a;">{format_currency_inr(result.projected_ending_balance)}</div>
                    <div style="font-size:0.82rem; color:#64748b; margin-top:0.5rem; line-height:1.6;">
                        &bull; Total Contributions: <b>{format_currency_inr(result.total_contributions)}</b><br>
                        &bull; Estimated Growth: <b>{format_currency_inr(max(0.0, result.estimated_growth))}</b><br>
                        &bull; Real Purchasing Power: <b>{format_currency_inr(result.inflation_adjusted_balance)}</b><br>
                        &bull; Assumed Return: <b>{result.config.annual_return:.1f}%</b><br>
                        &bull; Assumed Inflation: <b>{result.config.annual_inflation:.1f}%</b><br>
                        &bull; Monthly Contribution: <b>{format_currency_inr(result.config.monthly_contribution)}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Spread metric
    st.markdown("<br>", unsafe_allow_html=True)
    diff = explorer_result.optimism_pessimism_diff
    st.markdown(
        f"""
        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:1rem; text-align:center;">
            <span style="font-size:0.85rem; color:#64748b;">Optimistic − Pessimistic Spread:</span>
            <span style="font-size:1.4rem; font-weight:800; color:#4f46e5; margin-left:0.5rem;">{format_currency_inr(diff)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Charts ----
    st.markdown("<br>", unsafe_allow_html=True)
    tab_traj, tab_summary = st.tabs(["📈 Trajectory Chart", "📊 Outcome Summary Chart"])

    with tab_traj:
        fig_uncertainty = plot_uncertainty_scenario_trajectories(explorer_result.trajectory_df)
        render_plotly_chart(fig_uncertainty, key="chart_uncertainty_traj")

    with tab_summary:
        results_dict = {
            "optimistic": explorer_result.optimistic,
            "moderate": explorer_result.moderate,
            "pessimistic": explorer_result.pessimistic,
        }
        fig_uncertainty_bars = plot_uncertainty_summary_bars(results_dict)
        render_plotly_chart(fig_uncertainty_bars, key="chart_uncertainty_bars")

    # Plain-English explanation
    spread_explanation = explain_scenario_spread(explorer_result)
    st.markdown(
        f"""
        <div class="narrative-card" style="margin-top:1rem;">
            <div style="font-weight:700; font-size:1.05rem; color:#0f172a; margin-bottom:0.5rem;">
                💬 What this spread means
            </div>
            {spread_explanation}
        </div>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# PAGE 4: RECOMMENDATION ENGINE (MODULE 2)
# -----------------------------------------------------------------------------
elif st.session_state.current_page == "Recommendation Engine":
    render_page_header(
        breadcrumb="Intelligent Financial Recommendations",
        title="Recommendation Engine",
        subtitle="Rule-based evidence-driven recommendations derived from your actual financial inputs and calculated outcomes.",
    )

    st.markdown(
        """
        <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:12px; padding:1rem; margin-bottom:1.5rem;">
            <b>ℹ️ About This Engine:</b> Recommendations are generated dynamically using a deterministic
            rule-based engine — not an external AI API. Every recommendation is triggered by your actual
            calculated values and includes the specific reason it was raised and a practical next step.
            This is not certified financial advice.
        </div>
        """,
        unsafe_allow_html=True,
    )

    rec_inputs = st.session_state.inputs
    rec_target = st.session_state.target_goal

    # Run engine
    rec_report = generate_recommendations(rec_inputs, target_amount=rec_target)

    # Summary header
    summary_color = "#10b981" if rec_report.total_issues == 0 else ("#f43f5e" if any(r.severity == "critical" for r in rec_report.recommendations) else "#f59e0b")
    st.markdown(
        f"""
        <div style="background:#f8fafc; border-left:4px solid {summary_color}; border-radius:8px; padding:1rem; margin-bottom:1.5rem;">
            <b style="color:{summary_color};">Overall Assessment:</b> {rec_report.summary}
            <br><span style="font-size:0.85rem; color:#64748b;">Based on: {format_currency_inr(rec_inputs.monthly_income)}/mo income · {format_currency_inr(rec_inputs.monthly_contribution)}/mo contribution · {rec_inputs.duration_years}yr horizon · Target: {format_currency_inr(rec_target)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Quick stats
    qc1, qc2, qc3 = st.columns(3)
    with qc1:
        st.markdown(f"""<div class="metric-card"><div class="metric-card-label">Total Recommendations</div>
        <div class="metric-card-value">{len(rec_report.recommendations)}</div>
        <div class="metric-card-sub">Rules evaluated from your inputs</div></div>""", unsafe_allow_html=True)
    with qc2:
        st.markdown(f"""<div class="metric-card"><div class="metric-card-label">Issues Flagged</div>
        <div class="metric-card-value" style="color:#f59e0b;">{rec_report.total_issues}</div>
        <div class="metric-card-sub">Critical or warning-level findings</div></div>""", unsafe_allow_html=True)
    with qc3:
        st.markdown(f"""<div class="metric-card"><div class="metric-card-label">Positive Findings</div>
        <div class="metric-card-value" style="color:#10b981;">{rec_report.positive_findings}</div>
        <div class="metric-card-sub">Strengths identified in your plan</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if not rec_report.recommendations:
        st.markdown(
            """
            <div style="background:#fff; border:1px dashed #cbd5e1; border-radius:12px; padding:2rem; text-align:center; color:#64748b;">
                <div style="font-size:2rem; margin-bottom:0.5rem;">✅</div>
                <b>No issues detected.</b> Your financial plan is well-configured under current assumptions.
                Go to the Finance Simulator to adjust parameters and see updated recommendations.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        severity_order = {"critical": 0, "warning": 1, "info": 2, "positive": 3}
        sorted_recs = sorted(rec_report.recommendations, key=lambda r: severity_order.get(r.severity, 99))

        for i, rec in enumerate(sorted_recs):
            sev_colors = {
                "critical": ("#fff1f2", "#f43f5e", "🚨"),
                "warning":  ("#fffbeb", "#f59e0b", "⚠️"),
                "info":     ("#eff6ff", "#3b82f6", "ℹ️"),
                "positive": ("#ecfdf5", "#10b981", "✅"),
            }
            bg, border, icon = sev_colors.get(rec.severity, ("#f8fafc", "#94a3b8", "•"))
            metric_html = ""
            if rec.metric_label and rec.metric_value:
                metric_html = f"""<div style="display:inline-block; background:#f1f5f9; border-radius:6px; padding:2px 10px; font-size:0.82rem; color:#475569; margin-top:0.5rem;">
                    {rec.metric_label}: <b>{rec.metric_value}</b></div>"""

            st.markdown(
                f"""
                <div style="background:{bg}; border:1px solid {border}; border-radius:12px; padding:1.25rem; margin-bottom:1rem;">
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:0.5rem;">
                        <span style="font-size:1.1rem;">{icon}</span>
                        <span style="font-weight:700; font-size:1rem; color:#0f172a;">{rec.title}</span>
                        <span style="font-size:0.75rem; font-weight:600; color:{border}; background:rgba(0,0,0,0.05); border-radius:9999px; padding:2px 8px; margin-left:auto;">{rec.category}</span>
                    </div>
                    <div style="font-size:0.9rem; color:#334155; line-height:1.6; margin-bottom:0.6rem;">
                        <b>Why:</b> {rec.reason}
                    </div>
                    <div style="font-size:0.9rem; color:#1e293b; line-height:1.6; background:rgba(255,255,255,0.6); border-radius:6px; padding:0.5rem 0.75rem;">
                        <b>💡 Action:</b> {rec.action}
                    </div>
                    {metric_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Update finance parameters shortcut
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 **Tip:** Recommendations update automatically when you change parameters in the Finance Simulator. Navigate there to adjust your inputs and revisit this page.")


# -----------------------------------------------------------------------------
# PAGE 5 (was 3): SCENARIO COMPARISON
# -----------------------------------------------------------------------------
elif st.session_state.current_page == "Scenario Comparison":
    render_page_header(
        breadcrumb="Comparative Modeling",
        title="Multi-Scenario Comparison & Trade-Off Analysis",
        subtitle="Evaluate multiple financial trajectories side-by-side, analyze deltas against a selected baseline, and inspect ranking criteria.",
    )

    if not st.session_state.scenarios:
        st.session_state.scenarios = get_default_preset_scenarios(st.session_state.inputs)

    # Top Controls: Baseline selection and Scenario management
    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    with col_ctrl1:
        scenario_names = [s.name for s in st.session_state.scenarios]
        scenario_ids = [s.id for s in st.session_state.scenarios]
        
        current_baseline_idx = scenario_ids.index(st.session_state.baseline_id) if st.session_state.baseline_id in scenario_ids else 0
        selected_baseline_name = st.selectbox(
            "Select Baseline Scenario (to calculate deltas against):",
            options=scenario_names,
            index=current_baseline_idx,
        )
        st.session_state.baseline_id = st.session_state.scenarios[scenario_names.index(selected_baseline_name)].id

    with col_ctrl2:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if st.button("↺ Restore Default Presets", use_container_width=True):
            st.session_state.scenarios = get_default_preset_scenarios(st.session_state.inputs)
            st.session_state.baseline_id = "current_plan"
            st.rerun()

    # Generate Comparison Report
    comp_report = compare_scenarios(st.session_state.scenarios, baseline_id=st.session_state.baseline_id)

    # Multi-line Trajectory Comparison Chart
    traj_df = build_multi_scenario_trajectory_dataframe(st.session_state.scenarios)
    colors_map = {s.name: s.color for s in st.session_state.scenarios}
    fig_comp_lines = plot_scenario_comparison_trajectories(traj_df, colors_map)
    render_plotly_chart(fig_comp_lines, key="chart_scenarios")

    # Side-by-Side Comparison Metric Cards
    st.markdown(
        """
        <h3 style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.25rem; font-weight:700; color:#0f172a; margin-top:1.5rem; margin-bottom:0.75rem;">
            Scenario Breakdown vs Baseline
        </h3>
        """,
        unsafe_allow_html=True,
    )

    card_cols = st.columns(len(st.session_state.scenarios))
    baseline_scenario = next(s for s in st.session_state.scenarios if s.id == st.session_state.baseline_id)
    baseline_balance = baseline_scenario.outputs.projected_ending_balance

    for idx, s in enumerate(st.session_state.scenarios):
        with card_cols[idx]:
            out = s.outputs
            diff = out.projected_ending_balance - baseline_balance
            diff_sign = "+" if diff > 0 else ""
            diff_color = "#10b981" if diff > 0 else ("#f43f5e" if diff < 0 else "#64748b")
            diff_text = f"{diff_sign}{format_currency_inr(diff)}" if s.id != st.session_state.baseline_id else "Baseline Anchor"

            is_active_badge = " (Active Baseline)" if s.id == st.session_state.baseline_id else ""
            st.markdown(
                f"""
                <div class="metric-card" style="border-top:4px solid {s.color};">
                    <div class="metric-card-label">
                        <span>{s.name}{is_active_badge}</span>
                    </div>
                    <div class="metric-card-value">{format_currency_inr(out.projected_ending_balance)}</div>
                    <div style="font-size:0.85rem; font-weight:700; color:{diff_color}; margin:0.35rem 0;">
                        {diff_text}
                    </div>
                    <div style="font-size:0.82rem; color:#64748b; line-height:1.5; border-top:1px solid #f1f5f9; padding-top:0.4rem; margin-top:0.4rem;">
                        &bull; Monthly Deposit: <b>{format_currency_inr(out.inputs.monthly_contribution)}</b><br>
                        &bull; Total Contributed: <b>{format_currency_inr(out.total_contributed)}</b><br>
                        &bull; Return Assumption: <b>{out.inputs.annual_return:.1f}%</b><br>
                        &bull; Inflation Drag: <b>{out.inputs.annual_inflation:.1f}%</b><br>
                        &bull; Real Purchasing Power: <b>{format_currency_inr(out.inflation_adjusted_balance)}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Dynamic Narrative Insights
    if comp_report.insights:
        st.markdown(
            """
            <h3 style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.2rem; font-weight:700; color:#0f172a; margin-top:2rem; margin-bottom:0.5rem;">
                💡 Dynamic Trade-off Explanations
            </h3>
            """,
            unsafe_allow_html=True,
        )
        for ins in comp_report.insights:
            st.markdown(
                f"""
                <div class="narrative-card">
                    {ins}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Scenario Ranking by Objective Criteria
    st.markdown(
        """
        <h3 style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.2rem; font-weight:700; color:#0f172a; margin-top:2rem; margin-bottom:0.5rem;">
            🏆 Objective Scenario Rankings
        </h3>
        """,
        unsafe_allow_html=True,
    )
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-card-label">Highest Nominal Ending Balance</div>
                <div style="font-weight:700; color:#0f172a; margin-top:0.4rem;">1. {comp_report.rankings['highest_nominal'][0]}</div>
                <div style="font-size:0.85rem; color:#64748b;">2. {comp_report.rankings['highest_nominal'][1] if len(comp_report.rankings['highest_nominal']) > 1 else '-'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_r2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-card-label">Highest Real Purchasing Power</div>
                <div style="font-weight:700; color:#0f172a; margin-top:0.4rem;">1. {comp_report.rankings['highest_real_purchasing_power'][0]}</div>
                <div style="font-size:0.85rem; color:#64748b;">2. {comp_report.rankings['highest_real_purchasing_power'][1] if len(comp_report.rankings['highest_real_purchasing_power']) > 1 else '-'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_r3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-card-label">Highest Savings Rate Efficiency</div>
                <div style="font-weight:700; color:#0f172a; margin-top:0.4rem;">1. {comp_report.rankings['highest_savings_rate'][0]}</div>
                <div style="font-size:0.85rem; color:#64748b;">2. {comp_report.rankings['highest_savings_rate'][1] if len(comp_report.rankings['highest_savings_rate']) > 1 else '-'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Manage Scenarios (Rename, Delete)
    with st.expander("⚙️ Manage & Rename Saved Scenarios", expanded=False):
        for s in st.session_state.scenarios:
            col_m1, col_m2, col_m3 = st.columns([3, 2, 1])
            with col_m1:
                new_title = st.text_input(f"Scenario Label", value=s.name, key=f"title_{s.id}")
                s.name = new_title
            with col_m2:
                st.caption(f"ID: `{s.id}` | Duration: {s.inputs.duration_years}y | Contrib: {format_currency_inr(s.inputs.monthly_contribution)}")
            with col_m3:
                if len(st.session_state.scenarios) > 1:
                    if st.button("Delete", key=f"del_{s.id}"):
                        st.session_state.scenarios = [x for x in st.session_state.scenarios if x.id != s.id]
                        if st.session_state.baseline_id == s.id:
                            st.session_state.baseline_id = st.session_state.scenarios[0].id
                        st.rerun()



# -----------------------------------------------------------------------------
# PAGE (NEW): DATA SCIENCE EXPERIMENT LAB (MODULE 3)
# -----------------------------------------------------------------------------
elif st.session_state.current_page == "Data Science Experiment Lab":
    render_page_header(
        breadcrumb="Data Science Experiment Lab",
        title="Impact of Financial Variables on Long-Term Savings",
        subtitle="A Scenario-Based Sensitivity Analysis — Four controlled experiments investigating how key financial assumptions affect projected savings outcomes.",
    )

    st.markdown(
        """
        <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:12px; padding:1rem; margin-bottom:1.5rem;">
            <b>🔬 Experimental Design:</b> Each experiment follows a one-factor-at-a-time (OFAT) approach:
            one independent variable (IV) is varied while all other parameters are held constant (ceteris paribus).
            The dependent variable (DV) is the projected ending balance or real purchasing power.
            <b>No statistical inference or significance testing is performed.</b>
            Results are mathematical simulations, not real-world financial predictions.
        </div>
        """,
        unsafe_allow_html=True,
    )

    lab_base = st.session_state.inputs

    # Experiment selector
    exp_choice = st.radio(
        "Select Experiment:",
        options=[
            "A — Monthly Savings Contribution",
            "B — Annual Inflation Impact",
            "C — Investment Return Rate",
            "D — Time Horizon",
        ],
        horizontal=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ========================== EXPERIMENT A ==========================
    if exp_choice.startswith("A"):
        st.markdown(
            """<div class="feature-card" style="margin-bottom:1rem;">
                <b style="color:#4f46e5;">Experiment A: Monthly Savings Contribution</b><br>
                <span style="font-size:0.9rem; color:#64748b;">
                    <b>Independent Variable (IV):</b> Monthly savings contribution (₹/month)<br>
                    <b>Dependent Variable (DV):</b> Projected nominal ending balance (₹)<br>
                    <b>Held Constant:</b> Annual return, annual inflation, duration, initial savings
                </span>
            </div>""",
            unsafe_allow_html=True,
        )
        exp_a = run_experiment_a(lab_base)

        tab_a1, tab_a2, tab_a3 = st.tabs(["📈 Response Curve", "📊 Composition Chart", "📋 Data Table"])
        with tab_a1:
            fig_a = plot_experiment_response_curve(
                exp_a.data_frame, "Monthly_Contribution", "Monthly Contribution (₹/mo)",
                exp_a.title, subtitle=f"Fixed: {', '.join(f'{k}: {v}' for k, v in exp_a.fixed_parameters.items())}"
            )
            render_plotly_chart(fig_a, key="chart_exp_a_curve")
        with tab_a2:
            fig_a_bars = plot_experiment_grouped_bars(
                exp_a.data_frame, "Monthly_Contribution", "Monthly Contribution (₹/mo)", exp_a.title
            )
            render_plotly_chart(fig_a_bars, key="chart_exp_a_bars")
        with tab_a3:
            st.dataframe(exp_a.data_frame, use_container_width=True, hide_index=True)

        st.markdown(
            f"""<div class="narrative-card" style="margin-top:0.75rem;">
                <b>📝 Interpretation:</b> {exp_a.interpretation}
                <br><br><b>Outcome Spread:</b> {format_currency_inr(exp_a.min_outcome)} → {format_currency_inr(exp_a.max_outcome)}
                (range: <b>{format_currency_inr(exp_a.outcome_range)}</b>)
            </div>""",
            unsafe_allow_html=True,
        )

    # ========================== EXPERIMENT B ==========================
    elif exp_choice.startswith("B"):
        st.markdown(
            """<div class="feature-card" style="margin-bottom:1rem;">
                <b style="color:#4f46e5;">Experiment B: Annual Inflation Impact</b><br>
                <span style="font-size:0.9rem; color:#64748b;">
                    <b>Independent Variable (IV):</b> Annual inflation rate (%)<br>
                    <b>Dependent Variable (DV):</b> Real (inflation-adjusted) purchasing power (₹)<br>
                    <b>Held Constant:</b> Monthly contribution, annual return, duration, initial savings
                </span>
            </div>""",
            unsafe_allow_html=True,
        )
        exp_b = run_experiment_b(lab_base)

        tab_b1, tab_b2, tab_b3 = st.tabs(["📈 Response Curve", "📊 Composition Chart", "📋 Data Table"])
        with tab_b1:
            fig_b = plot_experiment_response_curve(
                exp_b.data_frame, "Annual_Inflation", "Annual Inflation Rate (%)",
                exp_b.title,
                y_col_nominal="Projected_Ending_Balance",
                y_col_real="Real_Purchasing_Power",
                subtitle=f"Fixed: {', '.join(f'{k}: {v}' for k, v in exp_b.fixed_parameters.items())}"
            )
            render_plotly_chart(fig_b, key="chart_exp_b_curve")
        with tab_b2:
            fig_b_bars = plot_experiment_grouped_bars(
                exp_b.data_frame, "Annual_Inflation", "Annual Inflation Rate (%)", exp_b.title
            )
            render_plotly_chart(fig_b_bars, key="chart_exp_b_bars")
        with tab_b3:
            st.dataframe(exp_b.data_frame, use_container_width=True, hide_index=True)

        st.markdown(
            f"""<div class="narrative-card" style="margin-top:0.75rem;">
                <b>📝 Interpretation:</b> {exp_b.interpretation}
                <br><br><b>Real Value Spread:</b> {format_currency_inr(exp_b.min_outcome)} → {format_currency_inr(exp_b.max_outcome)}
                (range: <b>{format_currency_inr(exp_b.outcome_range)}</b>)
            </div>""",
            unsafe_allow_html=True,
        )

    # ========================== EXPERIMENT C ==========================
    elif exp_choice.startswith("C"):
        st.markdown(
            """<div class="feature-card" style="margin-bottom:1rem;">
                <b style="color:#4f46e5;">Experiment C: Investment Return Rate</b><br>
                <span style="font-size:0.9rem; color:#64748b;">
                    <b>Independent Variable (IV):</b> Assumed annual return rate (%)<br>
                    <b>Dependent Variable (DV):</b> Projected nominal ending balance (₹)<br>
                    <b>Held Constant:</b> Monthly contribution, annual inflation, duration, initial savings
                </span>
            </div>""",
            unsafe_allow_html=True,
        )
        st.warning(
            "⚠️ **Return Rate Disclaimer:** These return rates are hypothetical user-specified assumptions "
            "for educational simulation purposes. They do NOT represent guaranteed investment outcomes. "
            "Actual returns are subject to market risk, volatility, and economic conditions."
        )
        exp_c = run_experiment_c(lab_base)

        tab_c1, tab_c2, tab_c3 = st.tabs(["📈 Response Curve", "📊 Composition Chart", "📋 Data Table"])
        with tab_c1:
            fig_c = plot_experiment_response_curve(
                exp_c.data_frame, "Annual_Return", "Assumed Annual Return Rate (%)",
                exp_c.title,
                subtitle=f"Fixed: {', '.join(f'{k}: {v}' for k, v in exp_c.fixed_parameters.items())}"
            )
            render_plotly_chart(fig_c, key="chart_exp_c_curve")
        with tab_c2:
            fig_c_bars = plot_experiment_grouped_bars(
                exp_c.data_frame, "Annual_Return", "Assumed Annual Return Rate (%)", exp_c.title
            )
            render_plotly_chart(fig_c_bars, key="chart_exp_c_bars")
        with tab_c3:
            st.dataframe(exp_c.data_frame, use_container_width=True, hide_index=True)

        st.markdown(
            f"""<div class="narrative-card" style="margin-top:0.75rem;">
                <b>📝 Interpretation:</b> {exp_c.interpretation}
                <br><br><b>Outcome Spread:</b> {format_currency_inr(exp_c.min_outcome)} → {format_currency_inr(exp_c.max_outcome)}
                (range: <b>{format_currency_inr(exp_c.outcome_range)}</b>)
            </div>""",
            unsafe_allow_html=True,
        )

    # ========================== EXPERIMENT D ==========================
    elif exp_choice.startswith("D"):
        st.markdown(
            """<div class="feature-card" style="margin-bottom:1rem;">
                <b style="color:#4f46e5;">Experiment D: Time Horizon</b><br>
                <span style="font-size:0.9rem; color:#64748b;">
                    <b>Independent Variable (IV):</b> Simulation duration (years)<br>
                    <b>Dependent Variable (DV):</b> Projected nominal ending balance (₹)<br>
                    <b>Held Constant:</b> Monthly contribution, annual return, annual inflation, initial savings
                </span>
            </div>""",
            unsafe_allow_html=True,
        )
        exp_d = run_experiment_d(lab_base)

        tab_d1, tab_d2, tab_d3 = st.tabs(["📈 Response Curve", "📊 Composition Chart", "📋 Data Table"])
        with tab_d1:
            fig_d = plot_experiment_response_curve(
                exp_d.data_frame, "Duration_Years", "Time Horizon (Years)",
                exp_d.title,
                subtitle=f"Fixed: {', '.join(f'{k}: {v}' for k, v in exp_d.fixed_parameters.items())}"
            )
            render_plotly_chart(fig_d, key="chart_exp_d_curve")
        with tab_d2:
            fig_d_bars = plot_experiment_grouped_bars(
                exp_d.data_frame, "Duration_Years", "Time Horizon (Years)", exp_d.title
            )
            render_plotly_chart(fig_d_bars, key="chart_exp_d_bars")
        with tab_d3:
            st.dataframe(exp_d.data_frame, use_container_width=True, hide_index=True)

        st.markdown(
            f"""<div class="narrative-card" style="margin-top:0.75rem;">
                <b>📝 Interpretation:</b> {exp_d.interpretation}
                <br><br><b>Outcome Spread:</b> {format_currency_inr(exp_d.min_outcome)} → {format_currency_inr(exp_d.max_outcome)}
                (range: <b>{format_currency_inr(exp_d.outcome_range)}</b>)
            </div>""",
            unsafe_allow_html=True,
        )

    # ---- Methodology Section ----
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📚 Experiment Methodology, Variables & Limitations", expanded=False):
        st.markdown(
            """
            ### Mathematical Model
            All experiments use the standard monthly compounding ordinary annuity formula:

            **Projected Ending Balance:**
            `FV = PV × (1 + r_m)^n + PMT × [((1 + r_m)^n − 1) / r_m]`

            Where:
            - `PV` = Initial savings balance
            - `PMT` = Monthly savings contribution
            - `r_m = (annual_return / 100) / 12` — monthly compounding rate
            - `n = duration_years × 12` — total months
            - `FV_annuity = PMT × n` when `r_m = 0` (L'Hôpital's rule)

            **Real Purchasing Power (Fisher Deflation):**
            `Real FV = FV / (1 + i)^t`

            Where `i = annual_inflation / 100` and `t = duration in years`.

            ### Experimental Variables
            | Experiment | Independent Variable | Dependent Variable | Fixed Parameters |
            |---|---|---|---|
            | A | Monthly Contribution | Nominal Ending Balance | Return, Inflation, Duration |
            | B | Annual Inflation Rate | Real Purchasing Power | Contribution, Return, Duration |
            | C | Annual Return Rate | Nominal Ending Balance | Contribution, Inflation, Duration |
            | D | Duration (Years) | Nominal Ending Balance | Contribution, Return, Inflation |

            ### Assumptions
            - Monthly compounding is used throughout (industry-standard convention).
            - Contributions occur at end of period (ordinary annuity) unless specified otherwise.
            - Zero-return edge case handled analytically (avoids division by zero).
            - All scenarios use the same initial savings balance from the Finance Simulator.

            ### Limitations
            - **No statistical inference:** No hypothesis testing or p-values are computed. Results describe mathematical relationships, not probability distributions.
            - **No real-world validation:** Projections are theoretical models. Actual financial outcomes depend on market volatility, behavioral factors, tax implications, and economic events beyond this model's scope.
            - **Point estimates only:** Each scenario produces a single deterministic projection, not a distribution of outcomes.
            - **Return assumptions are not guaranteed:** Higher assumed returns represent optimistic hypothetical scenarios only.
            - **Fixed-contribution model:** Does not account for income growth, step-up contributions, or irregular deposits.

            ### Interpretation of Results
            Observe the direction and magnitude of changes as the independent variable is varied.
            Non-linear acceleration at higher durations or returns demonstrates compound interest effects.
            The spread between minimum and maximum outcomes quantifies the sensitivity of the outcome to each variable.
            """,
            unsafe_allow_html=True,
        )

    # ---- Downloads ----
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """<h3 style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.15rem; font-weight:700; color:#0f172a; margin-bottom:0.75rem;">
            📥 Export Experiment Results
        </h3>""",
        unsafe_allow_html=True,
    )

    exp_a_dl = run_experiment_a(lab_base)
    exp_b_dl = run_experiment_b(lab_base)
    exp_c_dl = run_experiment_c(lab_base)
    exp_d_dl = run_experiment_d(lab_base)

    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        csv_export = export_experiment_results_csv(exp_a_dl, exp_b_dl, exp_c_dl, exp_d_dl)
        st.download_button(
            label="📊 Download All Experiment Results (CSV)",
            data=csv_export,
            file_name=f"WhatIf_AI_Experiments_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with dl_col2:
        txt_report = export_experiment_summary_report(exp_a_dl, exp_b_dl, exp_c_dl, exp_d_dl, lab_base)
        st.download_button(
            label="📄 Download Experiment Summary Report (TXT)",
            data=txt_report,
            file_name=f"WhatIf_AI_Experiment_Report_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True,
        )


# -----------------------------------------------------------------------------
# PAGE 4: DATA SCIENCE & SENSITIVITY ANALYSIS
# -----------------------------------------------------------------------------
elif st.session_state.current_page == "Data Science & Sensitivity":
    render_page_header(
        breadcrumb="Quantitative Scenario Analytics",
        title="Sensitivity Analysis & Decision Intelligence",
        subtitle="Identify which lifestyle parameters exert the highest mathematical elasticity on long-term wealth accumulation.",
    )

    base_inputs = st.session_state.inputs

    # Top Controls for Perturbation Range
    col_s1, col_s2 = st.columns([1, 2])
    with col_s1:
        perturbation = st.slider(
            "Local Perturbation Percentage (± %)",
            min_value=10,
            max_value=50,
            value=25,
            step=5,
            help="Symmetric percentage swing applied to test input parameters holding other variables constant.",
        )

    sens_report = compute_tornado_analysis(base_inputs, perturbation_pct=float(perturbation))

    with col_s2:
        st.markdown(
            f"""
            <div class="narrative-card narrative-card-success" style="margin-top:0.5rem;">
                🎯 <b>Primary Elasticity Driver:</b> <b>{sens_report.top_driver_name}</b> produces the single largest outcome swing of 
                <b>{format_currency_inr(sens_report.top_driver_swing)}</b> under ±{perturbation}% variance.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Tornado Plot
    fig_tornado = plot_tornado_sensitivity_chart(sens_report)
    render_plotly_chart(fig_tornado, key="chart_tornado")

    # Elasticity Metrics Table
    with st.expander("📊 Elasticity & Parameter Swing Details", expanded=True):
        tornado_rows = []
        for r in sens_report.ranked_by_impact:
            tornado_rows.append({
                "Parameter": r.display_name,
                "Base Value": r.base_value,
                "Low Bound Tested": r.low_value,
                "High Bound Tested": r.high_value,
                "Low Case Outcome": format_currency_inr(r.low_outcome),
                "High Case Outcome": format_currency_inr(r.high_outcome),
                "Outcome Swing (₹)": format_currency_inr(r.outcome_swing),
                "Normalized Elasticity": f"{r.elasticity:.2f}x",
            })
        st.dataframe(pd.DataFrame(tornado_rows), use_container_width=True, hide_index=True)

    # 1D Parameter Response Curves
    st.markdown(
        """
        <h3 style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.3rem; font-weight:700; color:#0f172a; margin-top:2.5rem; margin-bottom:0.5rem;">
            Continuous 1-Dimensional Response Sweeps
        </h3>
        <div style="font-size:0.92rem; color:#64748b; margin-bottom:1rem;">
            Inspect continuous functional responses across continuous parameter domains.
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_sw1, tab_sw2 = st.tabs(["💵 Monthly Contribution Sweep", "📈 Return Rate Sweep"])

    with tab_sw1:
        sweep_contrib_df = compute_1d_sweep_contribution(
            base_inputs,
            min_contrib=2000.0,
            max_contrib=max(30000.0, base_inputs.monthly_contribution * 2.5),
            steps=15,
        )
        fig_sw1 = plot_1d_sweep_curve(
            sweep_contrib_df,
            x_col="Monthly_Contribution",
            x_label="Monthly Contribution Target (₹/mo)",
            title="Ending Wealth Response vs. Monthly Contribution Target",
        )
        render_plotly_chart(fig_sw1, key="chart_sweep_contrib")

    with tab_sw2:
        sweep_ret_df = compute_1d_sweep_returns(
            base_inputs,
            min_return=0.0,
            max_return=16.0,
            steps=17,
        )
        fig_sw2 = plot_1d_sweep_curve(
            sweep_ret_df,
            x_col="Annual_Return",
            x_label="Assumed Annual Return Rate (%)",
            title="Ending Wealth Response vs. Annual Return Rate",
        )
        render_plotly_chart(fig_sw2, key="chart_sweep_returns")


# -----------------------------------------------------------------------------
# PAGE 5: INSIGHTS & METHODOLOGY
# -----------------------------------------------------------------------------
elif st.session_state.current_page == "Insights & Methodology":
    render_page_header(
        breadcrumb="Academic & Mathematical Documentation",
        title="Simulation Methodology & Mathematical Formulations",
        subtitle="Transparent documentation of compounding conventions, inflation discounting, sensitivity mathematics, and viva defense notes.",
    )

    st.markdown(
        """
        <div class="feature-card" style="margin-bottom:1.5rem;">
            <div style="font-size:1.15rem; font-weight:700; color:#0f172a; margin-bottom:0.5rem;">
                1. Monthly Compounding & Annuity Mathematics
            </div>
            <div style="font-size:0.95rem; color:#475569; line-height:1.6;">
                WhatIf AI computes multi-period accumulations by decomposing the future corpus into two distinct mathematical components:
                <br><br>
                <b>A. Lump-Sum Future Value of Opening Reserves:</b><br>
                <code>FV<sub>lump</sub> = PV &times; (1 + r<sub>m</sub>)<sup>n</sup></code><br>
                Where <i>PV</i> is the current savings balance, <i>r<sub>m</sub> = (Annual Return / 100) / 12</i> is the nominal monthly compounding rate, and <i>n = Years &times; 12</i> is the total months.
                <br><br>
                <b>B. Ordinary Annuity of Recurring Monthly Contributions:</b><br>
                For regular end-of-month deposits (ordinary annuity convention):<br>
                <code>FV<sub>annuity</sub> = PMT &times; [((1 + r<sub>m</sub>)<sup>n</sup> - 1) / r<sub>m</sub>]</code><br>
                Where <i>PMT</i> is the monthly savings contribution. If <i>r<sub>m</sub> = 0</i>, L'Hôpital's rule yields <code>FV<sub>annuity</sub> = PMT &times; n</code>.
                <br><br>
                <b>Total Projected Ending Balance:</b><br>
                <code>Ending Balance = FV<sub>lump</sub> + FV<sub>annuity</sub></code>
            </div>
        </div>

        <div class="feature-card" style="margin-bottom:1.5rem;">
            <div style="font-size:1.15rem; font-weight:700; color:#0f172a; margin-bottom:0.5rem;">
                2. Inflation Discounting & Real Purchasing Power
            </div>
            <div style="font-size:0.95rem; color:#475569; line-height:1.6;">
                Nominal rupees accumulated 5 to 30 years in the future do not have constant purchasing power. To calculate real purchasing power, WhatIf AI applies the continuous Fisher purchasing power deflator:
                <br><br>
                <code>Real FV = FV<sub>nominal</sub> / (1 + i)<sup>t</sup></code><br>
                Where <i>i = Annual Inflation / 100</i> and <i>t = Duration in Years</i>.
                <br><br>
                The difference <code>Loss = FV<sub>nominal</sub> - Real FV</code> represents the cumulative inflation drag over the horizon.
            </div>
        </div>

        <div class="feature-card" style="margin-bottom:1.5rem;">
            <div style="font-size:1.15rem; font-weight:700; color:#0f172a; margin-bottom:0.5rem;">
                3. Sensitivity Analysis & Point Elasticity
            </div>
            <div style="font-size:0.95rem; color:#475569; line-height:1.6;">
                The sensitivity engine tests local partial derivatives numerically via the ceteris paribus (all else equal) perturbation method:
                <br><br>
                <code>Arc Elasticity = (% &Delta;Ending Balance) / (% &Delta;Input Parameter)</code><br>
                Variables are ranked in the Tornado diagram by total rupee outcome swing:
                <code>Swing = |Outcome(High Bound) - Outcome(Low Bound)|</code>.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # College Viva Preparation Q&A
    st.markdown(
        """
        <h3 style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.3rem; font-weight:700; color:#0f172a; margin-top:2rem; margin-bottom:0.75rem;">
            🎓 College Viva & Project Defense Guide
        </h3>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Q1: Why is this project built as a deterministic simulation rather than a machine learning model?", expanded=True):
        st.markdown(
            """
            **Examiner Answer:**
            Machine learning models are designed for pattern recognition and statistical inference over historical empirical datasets. However, personal financial scenario analysis is fundamentally a **conditional forward-simulation problem**:
            - Future individual cash flows depend on intentional user policy decisions (e.g. choosing to cut dining out or save ₹2,000 more), not stochastic historical regression.
            - Applying black-box neural networks or regressors would introduce unexplainable approximation errors into exact financial compounding laws.
            - Our Data Science contribution lies in **decision intelligence, multi-parameter sensitivity analysis, numerical elasticity ranking, and trade-off comparison**, which provides complete transparency and mathematical fidelity.
            """
        )

    with st.expander("Q2: How does WhatIf AI prevent misleading users about guaranteed investment returns?"):
        st.markdown(
            """
            **Examiner Answer:**
            The application strictly defaults the assumed return rate to **0%** (pure savings model). When users choose to experiment with non-zero returns:
            - The UI explicitly terms it an **assumed educational return**, not a guaranteed yield.
            - Asset composition charts explicitly segregate guaranteed contributed principal from estimated hypothetical compound growth.
            - Real purchasing power adjustments are displayed prominently to expose how inflation erodes nominal gains.
            """
        )

    with st.expander("Q3: How are budgetary constraints validated?"):
        st.markdown(
            """
            **Examiner Answer:**
            The application computes `monthly_surplus = income - (essential_expenses + discretionary_expenses)`. If `monthly_contribution > monthly_surplus`, a prominent warning flag is triggered, preventing users from assuming unrealistic savings without reconciling their expense structure.
            """
        )


# -----------------------------------------------------------------------------
# PAGE 6: ABOUT THE PROJECT
# -----------------------------------------------------------------------------
elif st.session_state.current_page == "About the Project":
    render_page_header(
        breadcrumb="Academic Project Information",
        title="About WhatIf AI",
        subtitle="7th-Semester B.Sc. Artificial Intelligence & Data Science Capstone Project.",
    )

    st.markdown(
        """
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:16px; padding:2rem; box-shadow:0 4px 6px -1px rgba(15,23,42,0.05); margin-bottom:1.5rem;">
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:1rem;">
                <div style="width:48px; height:48px; border-radius:12px; background:linear-gradient(135deg, #4f46e5, #7c3aed); display:flex; align-items:center; justify-content:center; color:#fff; font-size:1.5rem; font-weight:800;">
                    ⚡
                </div>
                <div>
                    <h2 style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.6rem; font-weight:800; color:#0f172a; margin:0;">WhatIf AI</h2>
                    <div style="font-size:0.88rem; color:#64748b;">An Interactive Decision Intelligence & Future Scenario Simulator</div>
                </div>
            </div>
            
            <p style="font-size:0.96rem; color:#334155; line-height:1.65;">
                <b>WhatIf AI</b> was conceived and engineered for the 7th-Semester B.Sc. in Artificial Intelligence and Data Science degree curriculum.
                The project bridges the gap between static descriptive budgeting dashboards and prescriptive decision support.
                By framing financial choices as an interactive conditional state-space, users can experiment with trade-offs before executing decisions.
            </p>

            <h4 style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.15rem; font-weight:700; color:#0f172a; margin-top:1.5rem; margin-bottom:0.5rem;">
                Technical Architecture & Clean Code Highlights
            </h4>
            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:1rem; margin-top:0.75rem;">
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:1rem;">
                    <div style="font-weight:700; color:#4f46e5; margin-bottom:0.25rem;">Modular Core Engine</div>
                    <div style="font-size:0.85rem; color:#64748b;">Decoupled <code>src/calculations.py</code> and <code>src/sensitivity.py</code> tested with automated pytest unit tests.</div>
                </div>
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:1rem;">
                    <div style="font-weight:700; color:#4f46e5; margin-bottom:0.25rem;">Custom UI Architecture</div>
                    <div style="font-size:0.85rem; color:#64748b;">Vanilla CSS design tokens, Inter typography, and Plotly color coordination eliminating default Streamlit aesthetics.</div>
                </div>
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:1rem;">
                    <div style="font-weight:700; color:#4f46e5; margin-bottom:0.25rem;">Zero External API Cost</div>
                    <div style="font-size:0.85rem; color:#64748b;">100% self-contained pure Python mathematical execution. No paid tokens, keys, or rate limits.</div>
                </div>
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:1rem;">
                    <div style="font-weight:700; color:#4f46e5; margin-bottom:0.25rem;">Automated Reporting</div>
                    <div style="font-size:0.85rem; color:#64748b;">Dynamic PDF synthesis powered by ReportLab with real-time scenario diffs and CSV schedule exports.</div>
                </div>
            </div>

            <h4 style="font-family:'Plus Jakarta Sans',sans-serif; font-size:1.15rem; font-weight:700; color:#0f172a; margin-top:1.5rem; margin-bottom:0.5rem;">
                Academic Project Report & Ethics Notice
            </h4>
            <div style="background:#fffbeb; border:1px solid #fde68a; border-radius:10px; padding:1rem; font-size:0.88rem; color:#92400e; line-height:1.6;">
                <b>Educational Disclaimer:</b> WhatIf AI is developed exclusively for academic evaluation, scenario modeling research, and decision-support demonstration. 
                Calculated figures represent mathematical projections based on user-supplied assumptions and do not constitute certified financial or investment advisory.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
