"""
Report Generator Module for WhatIf AI.

Generates:
1. Publication-quality PDF reports via ReportLab with executive summary, input assumptions,
   key results, scenario comparisons, annual amortization schedule, and methodology.
2. Formatted CSV datasets for user offline modeling in Excel.
"""

import io
from datetime import datetime
from typing import List, Optional
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from src.calculations import (
    SimulationInputs,
    SimulationOutputs,
    format_currency_inr,
    generate_yearly_schedule,
)
from src.scenarios import Scenario


def generate_pdf_report(
    scenario_name: str,
    inputs: SimulationInputs,
    outputs: SimulationOutputs,
    comparison_scenarios: Optional[List[Scenario]] = None,
) -> io.BytesIO:
    """
    Generates an executive-ready PDF report buffer with ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b"),
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("WhatIf AI &mdash; Decision Intelligence Report", title_style))
    current_time_str = datetime.now().strftime("%B %d, %Y - %H:%M")
    story.append(
        Paragraph(
            f"Scenario: <b>{scenario_name}</b> | Generated: {current_time_str} | B.Sc. Data Science Project Demonstration",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4f46e5"), spaceAfter=12))

    # 2. Executive Summary Metrics Table
    story.append(Paragraph("1. Executive Summary & Core Results", heading_style))
    
    summary_data = [
        [
            Paragraph("<b>Projected Ending Balance</b>", body_style),
            Paragraph(f"<b>{format_currency_inr(outputs.projected_ending_balance)}</b>", body_style),
            Paragraph("<b>Total Monthly Contributions</b>", body_style),
            Paragraph(f"{format_currency_inr(outputs.total_contributed)}", body_style),
        ],
        [
            Paragraph("<b>Estimated Compound Growth</b>", body_style),
            Paragraph(f"{format_currency_inr(outputs.estimated_growth)}", body_style),
            Paragraph("<b>Real Purchasing Power</b>", body_style),
            Paragraph(f"{format_currency_inr(outputs.inflation_adjusted_balance)}", body_style),
        ],
        [
            Paragraph("<b>Inflation Drag (Loss)</b>", body_style),
            Paragraph(f"{format_currency_inr(outputs.purchasing_power_loss)}", body_style),
            Paragraph("<b>Monthly Surplus</b>", body_style),
            Paragraph(f"{format_currency_inr(outputs.monthly_surplus)}", body_style),
        ],
    ]

    summary_table = Table(summary_data, colWidths=[140, 125, 140, 135])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 10))

    # 3. Input Assumptions Table
    story.append(Paragraph("2. Input Assumptions & Parameters", heading_style))
    assumptions_data = [
        ["Parameter", "Assumption Value", "Parameter", "Assumption Value"],
        ["Monthly Take-Home Income", format_currency_inr(inputs.monthly_income), "Simulation Duration", f"{inputs.duration_years} Years ({inputs.duration_years*12} mo)"],
        ["Monthly Essential Expenses", format_currency_inr(inputs.essential_expenses), "Annual Inflation Assumption", f"{inputs.annual_inflation:.2f}% per year"],
        ["Monthly Discretionary Expenses", format_currency_inr(inputs.discretionary_expenses), "Annual Return Assumption", f"{inputs.annual_return:.2f}% per year"],
        ["Starting Savings Balance", format_currency_inr(inputs.current_savings), "Contribution Timing", "End of month (Ordinary Annuity)"],
        ["Monthly Savings Target", format_currency_inr(inputs.monthly_contribution), "Savings Rate (% of Income)", f"{outputs.savings_rate:.1f}%"],
    ]

    assumptions_table = Table(assumptions_data, colWidths=[140, 125, 140, 135])
    assumptions_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e7ff")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#312e81")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(assumptions_table)
    story.append(Spacer(1, 10))

    # 4. Optional Scenario Comparison Section
    if comparison_scenarios and len(comparison_scenarios) > 1:
        story.append(Paragraph("3. Multi-Scenario Comparative Analysis", heading_style))
        comp_data = [
            ["Scenario Name", "Monthly Contrib.", "Return", "Ending Balance", "Real Value", "Delta to Active"]
        ]
        base_balance = outputs.projected_ending_balance
        for sc in comparison_scenarios:
            sc_out = sc.outputs or sc.evaluate()
            diff = sc_out.projected_ending_balance - base_balance
            diff_str = f"+{format_currency_inr(diff)}" if diff > 0 else (format_currency_inr(diff) if diff < 0 else "Baseline")
            comp_data.append([
                sc.name,
                format_currency_inr(sc.inputs.monthly_contribution),
                f"{sc.inputs.annual_return:.1f}%",
                format_currency_inr(sc_out.projected_ending_balance),
                format_currency_inr(sc_out.inflation_adjusted_balance),
                diff_str,
            ])

        comp_table = Table(comp_data, colWidths=[120, 85, 60, 95, 90, 90])
        comp_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(comp_table)
        story.append(Spacer(1, 10))

    # 5. Annual Projection Schedule (Snapshot up to 10 years or all)
    yearly_df = generate_yearly_schedule(inputs)
    if not yearly_df.empty:
        story.append(Paragraph("4. Annual Projection Schedule", heading_style))
        sched_data = [
            ["Year", "Starting Bal.", "Contrib. Added", "Growth Added", "Ending Balance", "Real Purchasing Power"]
        ]
        # Show all or sample
        for _, row in yearly_df.iterrows():
            sched_data.append([
                f"Year {int(row['Year'])}",
                format_currency_inr(row["Starting_Balance"]),
                format_currency_inr(row["Annual_Contributions"]),
                format_currency_inr(row["Annual_Growth"]),
                format_currency_inr(row["Ending_Balance"]),
                format_currency_inr(row["Real_Ending_Balance"]),
            ])

        sched_table = Table(sched_data, colWidths=[65, 95, 95, 95, 95, 95])
        sched_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2f6")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(KeepTogether(sched_table))
        story.append(Spacer(1, 10))

    # 6. Methodology & Viva Disclaimer
    story.append(Paragraph("5. Mathematical Methodology & Limitations", heading_style))
    method_text = (
        "<b>Mathematical Modeling:</b> Compound accumulations are computed using standard monthly compounding "
        "conventions: <i>FV = PV*(1 + r/12)^n + PMT*[((1 + r/12)^n - 1) / (r/12)]</i> where <i>r</i> is the annual return "
        "and <i>n</i> is the total number of months. Real purchasing power discounts nominal balances using the Fisher relation "
        "and stated inflation rates: <i>Real FV = FV / (1 + i)^t</i>.<br/><br/>"
        "<b>Notice & Academic Disclaimer:</b> This report is generated by WhatIf AI as part of a 7th-semester B.Sc. Artificial Intelligence "
        "and Data Science project. Calculations serve an educational and decision-support purpose only. Projections do not constitute "
        "financial advice, nor do they guarantee future returns."
    )
    story.append(Paragraph(method_text, disclaimer_style))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_csv_export(inputs: SimulationInputs) -> str:
    """
    Generates a CSV string of the annual projection schedule.
    """
    yearly_df = generate_yearly_schedule(inputs)
    return yearly_df.to_csv(index=False)
