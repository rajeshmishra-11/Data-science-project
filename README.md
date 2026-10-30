# WhatIf AI — Interactive Decision Intelligence & Future Scenario Simulator

> **B.Sc. Artificial Intelligence & Data Science — 7th Semester Capstone Project**

**Version:** 2.0.0 | **Framework:** Streamlit | **Language:** Python 3.10+

---

## ⚡ Project Overview

**WhatIf AI** is an interactive, data-driven **decision-support and scenario simulation platform** for personal financial planning. It enables users to explore "what if" questions about their savings, spending habits, and economic assumptions — visualising the impact of these decisions before they are made.

> **Important Disclaimer:** WhatIf AI is a mathematical simulation tool for educational and academic purposes. All projections are hypothetical and depend entirely on user-supplied assumptions. Calculated figures do not constitute certified financial advice or guaranteed investment forecasts.

---

## 🎯 Problem Statement

Traditional budget trackers are **descriptive** (they record what happened). WhatIf AI is **prescriptive and prospective**: it answers conditional "what if" questions about the future.

**Core problem:** How do changes in monthly savings contribution, inflation, investment return assumptions, and time horizon affect long-term wealth accumulation? Which variables exert the greatest mathematical influence on outcomes?

---

## 📐 Project Scope

WhatIf AI v2.0 addresses:

1. **Financial Simulation** — Multi-year compound savings projections with monthly granularity
2. **Uncertainty Analysis** — Three-scenario (Optimistic / Moderate / Pessimistic) exploration
3. **Rule-Based Recommendations** — Evidence-driven, dynamically generated financial guidance
4. **Scenario Comparison** — Multi-scenario side-by-side delta analysis
5. **Data Science Experiment Lab** — Four controlled OFAT sensitivity experiments
6. **Sensitivity Analysis** — Tornado chart and 1D parameter sweep visualisations
7. **Automated Testing** — 66 pytest unit tests across all modules
8. **Report Generation** — PDF executive reports and CSV data exports

---

## 🏗️ System Architecture

```
whatif-ai/
├── app.py                          # Main Streamlit application (9 pages)
├── src/
│   ├── calculations.py             # Core financial calculation engine
│   ├── scenarios.py                # Scenario management & comparison
│   ├── sensitivity.py              # Tornado & 1D sweep analysis
│   ├── visualizations.py           # All Plotly chart generators
│   ├── ui_components.py            # Reusable Streamlit HTML/CSS components
│   ├── report_generator.py         # PDF (ReportLab) & CSV export
│   ├── recommendation_engine.py    # Rule-based recommendation system (NEW v2.0)
│   ├── uncertainty_analysis.py     # Future Scenario Explorer (NEW v2.0)
│   └── experiment_lab.py           # Data Science Experiment Lab (NEW v2.0)
├── tests/
│   ├── test_calculations.py        # Core financial math tests (8 tests)
│   ├── test_scenarios.py           # Scenario comparison tests (3 tests)
│   ├── test_sensitivity.py         # Sensitivity analysis tests (2 tests)
│   ├── test_visualizations.py      # Chart generation tests (3 tests)
│   ├── test_exports.py             # PDF & CSV export tests (2 tests)
│   ├── test_app_flow.py            # Navigation flow tests (5 tests)
│   └── test_new_modules.py         # New module tests — 43 tests (NEW v2.0)
├── assets/
│   └── style.css                   # Custom SaaS design system
├── .streamlit/
│   └── config.toml                 # Streamlit configuration
├── requirements.txt
└── README.md
```

---

## 🔧 Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Application Framework | Streamlit ≥ 1.35 | Interactive web UI |
| Data Processing | pandas ≥ 2.0, NumPy ≥ 1.24 | DataFrames & numerical computation |
| Visualisations | Plotly ≥ 5.18 | Interactive charts |
| PDF Reporting | ReportLab ≥ 4.0 | Executive report generation |
| Testing | pytest ≥ 8.0 | Unit and integration tests |
| Styling | Vanilla CSS | Custom SaaS design tokens |
| Language | Python 3.10+ | Core logic |

---

## 📊 Data Science Methodology

### 1. Mathematical Model — Monthly Compounding Ordinary Annuity

The core financial projection uses standard compound interest mathematics:

**Future Value of Lump Sum (Initial Savings):**
```
FV_lump = PV × (1 + r_m)^n
```

**Future Value of Monthly Annuity (Contributions):**
```
FV_annuity = PMT × [((1 + r_m)^n - 1) / r_m]     [ordinary annuity: end-of-month]
FV_annuity = PMT × [((1 + r_m)^n - 1) / r_m] × (1 + r_m)  [annuity due: beginning-of-month]
```

**Zero Return Case (L'Hôpital's Rule):**
```
FV = PV + PMT × n
```

**Total Projected Ending Balance:**
```
FV_total = FV_lump + FV_annuity
```

Where:
- `PV` = Initial savings balance (₹)
- `PMT` = Monthly savings contribution (₹)
- `r_m = (annual_return / 100) / 12` — nominal monthly rate
- `n = duration_years × 12` — total months

### 2. Inflation Discounting — Fisher Deflation Formula

```
Real FV = FV_nominal / (1 + i)^t
```

Where `i = annual_inflation / 100` and `t = simulation duration in years`.

**Effective Real Return Rate (Fisher Equation):**
```
r_real = (1 + r_nominal) / (1 + i) - 1
```

### 3. Sensitivity Analysis — Ceteris Paribus Perturbation

```
Arc Elasticity = (% ΔOutcome) / (% ΔInput)
Tornado Swing = |Outcome(High Bound) - Outcome(Low Bound)|
```

Each variable is tested independently by ±perturbation% while all others are held constant.

### 4. Break-Even / Target Feasibility Analysis

For zero return:
```
Required PMT = (Target - PV) / n
```

For non-zero return (ordinary annuity):
```
Required PMT = (Target - PV × (1+r_m)^n) / [((1+r_m)^n - 1) / r_m]
```

Time to reach target (analytic solution):
```
n = log[(Target × r_m + PMT) / (PV × r_m + PMT)] / log(1 + r_m)
```

---

## 🔬 Experiment Design — Data Science Experiment Lab

**Project Title:** *Impact of Financial Variables on Long-Term Savings: A Scenario-Based Sensitivity Analysis*

**Experimental Design:** One-factor-at-a-time (OFAT) controlled simulations

| Experiment | Independent Variable (IV) | Dependent Variable (DV) | Fixed Parameters |
|---|---|---|---|
| A — Monthly Contribution | Monthly savings amount (₹/mo) | Nominal ending balance | Return, Inflation, Duration |
| B — Inflation Impact | Annual inflation rate (%) | Real purchasing power | Contribution, Return, Duration |
| C — Investment Return | Assumed annual return (%) | Nominal ending balance | Contribution, Inflation, Duration |
| D — Time Horizon | Simulation duration (years) | Nominal ending balance | Contribution, Return, Inflation |

**Key Findings:**
- Relationship A (Contribution → Balance): Linear when return=0, super-linear with compounding
- Relationship B (Inflation → Real Value): Monotonically decreasing (exponential decay)
- Relationship C (Return → Balance): Non-linear acceleration at longer durations
- Relationship D (Duration → Balance): Exponential growth with non-zero return rates

**Limitations:**
- No statistical significance testing (these are deterministic simulations, not probabilistic models)
- No real-world validation — outcomes depend on market volatility, behavioral factors, and events outside the model's scope
- Fixed contribution model — no step-up SIP, income growth, or irregular deposits
- Return assumptions are entirely hypothetical

---

## 🧠 Recommendation Engine

A **rule-based deterministic recommendation engine** (not an external AI API) that evaluates 11 rules against real-time calculated values:

| Rule | Trigger Condition | Severity |
|---|---|---|
| 1 | Total expenses > Monthly income | Critical |
| 2 | Monthly contribution > Available surplus | Warning |
| 3 | Discretionary expenses > 35% of income | Warning |
| 4 | Savings rate < 10% | Info |
| 5 | Goal achievable at current rate | Positive |
| 6 | Goal requires higher contribution (within surplus) | Warning |
| 7 | Goal unachievable within budget | Critical |
| 8 | Inflation erodes >20% of purchasing power | Info |
| 9 | Return = 0% with duration ≥ 3 years | Info |
| 10 | Duration < 10 years | Info |
| 11 | Initial savings > 24× monthly contribution with return > 0% | Positive |

Each recommendation includes: **category, severity, title, reason (why triggered), and a concrete action step.**

---

## 🔮 Future Scenario Explorer (Uncertainty Analysis)

Three-scenario framework for uncertainty quantification:

| Scenario | Contribution | Return | Inflation |
|---|---|---|---|
| Optimistic | Base × 1.2 | Base + 3% | Base − 1.5% |
| Moderate | Base (user inputs) | Base | Base |
| Pessimistic | Base × 0.8 | Base − 3% | Base + 2% |

All scenarios are fully user-configurable. The spread between Optimistic and Pessimistic outcomes quantifies the mathematical uncertainty range — not a statistical probability interval.

---

## 🧪 Testing Methodology

**Total Tests:** 66 (all pass)

```
pytest tests/ -v
```

| Test File | Tests | Coverage Area |
|---|---|---|
| test_calculations.py | 8 | Core math, compounding, inflation, formatting |
| test_scenarios.py | 3 | Preset generation, comparison, trajectory data |
| test_sensitivity.py | 2 | Tornado analysis, 1D sweeps |
| test_visualizations.py | 3 | Chart generation, layout, Plotly config |
| test_exports.py | 2 | PDF generation, CSV export |
| test_app_flow.py | 5 | Navigation pages |
| test_new_modules.py | 43 | Recommendation engine, uncertainty analysis, experiment lab |

**Test strategies used:**
- Mathematical identity verification (e.g., zero return = pure arithmetic)
- Monotonicity tests (higher contribution → higher balance)
- Cross-module consistency (experiment results match direct calculations)
- Edge case testing (zero income, zero return, single data point)
- Schema validation (DataFrame columns, DataClass fields)

---

## 📈 Application Pages

| # | Page | Description |
|---|---|---|
| 1 | 🏠 Overview | Platform introduction with live preview |
| 2 | 💼 Finance Simulator | Core multi-year compound savings calculator |
| 3 | 🔮 Future Scenario Explorer | Optimistic/Moderate/Pessimistic analysis (NEW) |
| 4 | 💡 Recommendation Engine | Rule-based financial guidance (NEW) |
| 5 | ⚖️ Scenario Comparison | Multi-scenario delta analysis |
| 6 | 🧪 Data Science Experiment Lab | OFAT sensitivity experiments (NEW) |
| 7 | 🔬 Data Science & Sensitivity | Tornado chart and parameter sweeps |
| 8 | 📖 Insights & Methodology | Mathematical documentation and viva guide |
| 9 | 🎓 About the Project | Academic information and ethics notice |

---

## 🚀 Installation & Deployment Guide

### 1. Local Environment Setup

#### Prerequisites
- **Python 3.10, 3.11, 3.12, or 3.13** installed
- **Git** version control tool

#### Step-by-Step Installation

```bash
# 1. Clone the repository
git clone https://github.com/rajeshmishra-11/Data-science-project.git
cd Data-science-project

# 2. Create an isolated virtual environment
# On Windows (PowerShell / Command Prompt):
python -m venv venv
.\venv\Scripts\activate

# On macOS / Linux:
python3 -m venv venv
source venv/bin/activate

# 3. Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Verify installation by running automated test suite
pytest tests/ -v

# 5. Launch the application locally
streamlit run app.py
```

The application will automatically open in your default browser at `http://localhost:8501`.

---

### 2. Preparing and Uploading to GitHub

Follow these steps to initialize and push your clean project repository to GitHub:

```bash
# 1. Navigate to the project directory
cd /path/to/data-science-project

# 2. Initialize a fresh git repository (if not already initialized)
git init

# 3. Verify .gitignore is in place to exclude caches and virtual environments
git status

# 4. Stage all project files
git add .

# 5. Commit project code
git commit -m "feat: release WhatIf AI v2.0 academic capstone project"

# 6. Ensure default branch is main
git branch -M main

# 7. Add your GitHub remote repository
git remote add origin https://github.com/rajeshmishra-11/Data-science-project.git

# 8. Push to GitHub
git push -u origin main
```

---

### 3. Deploying to Streamlit Community Cloud (Free Public Hosting)

Streamlit Community Cloud allows free, one-click hosting directly connected to your GitHub repository:

#### Deployment Steps:
1. **Sign In**: Go to **[share.streamlit.io](https://share.streamlit.io)** and log in using your GitHub account.
2. **New Application**: Click the **"New app"** button in the dashboard.
3. **Repository Details**:
   - **Repository**: Select `rajeshmishra-11/Data-science-project`
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. **Advanced Settings (Optional)**:
   - Python Version: Select `3.10`, `3.11`, or `3.12`
   - No external secrets/environment variables are required (WhatIf AI uses client-side computation).
5. **Deploy**: Click **"Deploy!"**.
   - Streamlit will provision the container, automatically install dependencies from `requirements.txt`, and start the app.
   - Your application will be live at a public URL (e.g., `https://whatif-ai.streamlit.app`).

#### Deployment Verification Checklist:
- [x] `app.py` is at root level as the primary entry point.
- [x] `requirements.txt` contains pinned/minimum compatible package versions.
- [x] `.streamlit/config.toml` has `headless = true` and custom theme configurations.
- [x] `assets/style.css` is loaded using OS-agnostic relative paths (`os.path.join`).
- [x] In-memory PDF/CSV generation via `io.BytesIO` / `io.StringIO` requires no file system write permissions.
- [x] 100% client-side deterministic mathematics; zero external API keys or database connections required.

---

### 4. Running the Automated Test Suite

```bash
# Run all 66 unit & integration tests
pytest tests/ -v

# Run with concise tracebacks
pytest tests/ -v --tb=short

# Run specific module tests
pytest tests/test_new_modules.py -v
pytest tests/test_calculations.py -v
```

---

## ⚠️ Known Limitations

1. **Point-estimate projections only** — no Monte Carlo or stochastic distribution modelling
2. **Fixed contribution model** — doesn't account for income growth or step-up SIP
3. **Tax not modelled** — all calculations are pre-tax
4. **No market data integration** — return rates are entirely user-specified assumptions
5. **Single-currency (INR)** — formatted specifically for Indian Rupee
6. **No user accounts or persistence** — session state is lost on page refresh
7. **Experiment Lab runs fresh calculations on every render** — consider caching for large datasets

---

## 🔮 Future Enhancements

- Monte Carlo simulation for probability distributions of outcomes
- Step-up SIP modelling (increasing contributions over time)
- Tax-adjusted real return calculations
- Multi-goal planning (house, education, retirement simultaneously)
- Historical inflation data integration
- User account persistence with cloud storage
- Mobile-responsive layout refinements
- Additional languages and currency support

---

## 📋 Ethics & Academic Notice

WhatIf AI was developed exclusively for academic evaluation, scenario-modelling research, and decision-support demonstration as part of a B.Sc. Artificial Intelligence and Data Science curriculum. Calculated figures are mathematical projections based on user-supplied assumptions and do not constitute certified financial or investment advisory. The application does not use external AI APIs or fabricate personalised advice.

---

*WhatIf AI v2.0 — B.Sc. AI & Data Science Capstone Project*
